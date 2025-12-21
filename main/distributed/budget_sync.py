"""
Distributed Budget Sync (v3.0)

分布式预算同步，确保跨实例的预算一致性。
"""
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from threading import Lock, Thread
import hashlib
import json


@dataclass
class BudgetState:
    """预算状态"""
    user_id: str
    total_budget: float
    consumed_budget: float
    version: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def remaining_budget(self) -> float:
        return self.total_budget - self.consumed_budget
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "total_budget": self.total_budget,
            "consumed_budget": self.consumed_budget,
            "remaining_budget": self.remaining_budget,
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
        }
    
    def checksum(self) -> str:
        """计算状态校验和"""
        content = f"{self.user_id}:{self.total_budget}:{self.consumed_budget}:{self.version}"
        return hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class SyncOperation:
    """同步操作"""
    operation_id: str
    user_id: str
    operation_type: str  # "consume", "reset", "update"
    amount: float
    timestamp: datetime = field(default_factory=datetime.now)
    source_instance: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "source_instance": self.source_instance,
        }


class DistributedBudgetSync:
    """
    分布式预算同步器
    
    提供:
    - 跨实例预算同步
    - 分布式锁
    - 冲突解决
    - 最终一致性保证
    """
    
    def __init__(
        self,
        instance_id: str,
        sync_interval_seconds: float = 1.0,
        lock_timeout_seconds: float = 5.0,
    ):
        """
        初始化分布式预算同步器
        
        Args:
            instance_id: 当前实例ID
            sync_interval_seconds: 同步间隔
            lock_timeout_seconds: 锁超时时间
        """
        self.instance_id = instance_id
        self.sync_interval = sync_interval_seconds
        self.lock_timeout = lock_timeout_seconds
        
        self._local_state: Dict[str, BudgetState] = {}
        self._pending_operations: List[SyncOperation] = []
        self._lock = Lock()
        
        # 分布式锁状态
        self._locks: Dict[str, Dict[str, Any]] = {}
        
        # 同步回调
        self._sync_callbacks: List[Callable] = []
        
        # 同步线程
        self._sync_thread: Optional[Thread] = None
        self._stop_sync = False
    
    def get_budget_state(self, user_id: str) -> Optional[BudgetState]:
        """获取用户预算状态"""
        with self._lock:
            return self._local_state.get(user_id)
    
    def set_budget_state(self, user_id: str, total_budget: float, consumed_budget: float = 0.0):
        """设置用户预算状态"""
        with self._lock:
            if user_id in self._local_state:
                state = self._local_state[user_id]
                state.total_budget = total_budget
                state.consumed_budget = consumed_budget
                state.version += 1
                state.last_updated = datetime.now()
            else:
                self._local_state[user_id] = BudgetState(
                    user_id=user_id,
                    total_budget=total_budget,
                    consumed_budget=consumed_budget,
                )
    
    def acquire_lock(self, user_id: str, timeout: float = None) -> bool:
        """
        获取用户预算的分布式锁
        
        Args:
            user_id: 用户ID
            timeout: 超时时间
            
        Returns:
            是否成功获取锁
        """
        timeout = timeout or self.lock_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._lock:
                if user_id not in self._locks:
                    self._locks[user_id] = {
                        "holder": self.instance_id,
                        "acquired_at": datetime.now(),
                    }
                    return True
                
                # 检查锁是否过期
                lock_info = self._locks[user_id]
                elapsed = (datetime.now() - lock_info["acquired_at"]).total_seconds()
                
                if elapsed > self.lock_timeout:
                    # 锁已过期，可以获取
                    self._locks[user_id] = {
                        "holder": self.instance_id,
                        "acquired_at": datetime.now(),
                    }
                    return True
            
            time.sleep(0.01)
        
        return False
    
    def release_lock(self, user_id: str) -> bool:
        """释放分布式锁"""
        with self._lock:
            if user_id in self._locks:
                if self._locks[user_id]["holder"] == self.instance_id:
                    del self._locks[user_id]
                    return True
            return False
    
    def consume_budget(self, user_id: str, amount: float) -> bool:
        """
        消耗预算 (带分布式锁)
        
        Args:
            user_id: 用户ID
            amount: 消耗量
            
        Returns:
            是否成功消耗
        """
        if not self.acquire_lock(user_id):
            return False
        
        try:
            with self._lock:
                state = self._local_state.get(user_id)
                if not state:
                    return False
                
                if state.remaining_budget < amount:
                    return False
                
                state.consumed_budget += amount
                state.version += 1
                state.last_updated = datetime.now()
                
                # 记录操作
                operation = SyncOperation(
                    operation_id=f"op_{int(time.time() * 1000)}_{self.instance_id}",
                    user_id=user_id,
                    operation_type="consume",
                    amount=amount,
                    source_instance=self.instance_id,
                )
                self._pending_operations.append(operation)
                
                return True
        finally:
            self.release_lock(user_id)
    
    def reset_budget(self, user_id: str) -> bool:
        """重置用户预算"""
        if not self.acquire_lock(user_id):
            return False
        
        try:
            with self._lock:
                state = self._local_state.get(user_id)
                if not state:
                    return False
                
                old_consumed = state.consumed_budget
                state.consumed_budget = 0.0
                state.version += 1
                state.last_updated = datetime.now()
                
                # 记录操作
                operation = SyncOperation(
                    operation_id=f"op_{int(time.time() * 1000)}_{self.instance_id}",
                    user_id=user_id,
                    operation_type="reset",
                    amount=old_consumed,
                    source_instance=self.instance_id,
                )
                self._pending_operations.append(operation)
                
                return True
        finally:
            self.release_lock(user_id)
    
    def get_pending_operations(self) -> List[SyncOperation]:
        """获取待同步的操作"""
        with self._lock:
            return list(self._pending_operations)
    
    def apply_remote_operation(self, operation: SyncOperation) -> bool:
        """
        应用远程操作
        
        Args:
            operation: 远程操作
            
        Returns:
            是否成功应用
        """
        if operation.source_instance == self.instance_id:
            return True  # 忽略自己的操作
        
        with self._lock:
            state = self._local_state.get(operation.user_id)
            if not state:
                return False
            
            if operation.operation_type == "consume":
                state.consumed_budget += operation.amount
            elif operation.operation_type == "reset":
                state.consumed_budget = 0.0
            
            state.version += 1
            state.last_updated = datetime.now()
            
            return True
    
    def sync_state(self, remote_states: Dict[str, BudgetState]):
        """
        同步远程状态
        
        使用版本号解决冲突，较高版本获胜
        """
        with self._lock:
            for user_id, remote_state in remote_states.items():
                local_state = self._local_state.get(user_id)
                
                if not local_state:
                    # 本地没有，直接使用远程状态
                    self._local_state[user_id] = remote_state
                elif remote_state.version > local_state.version:
                    # 远程版本更高，使用远程状态
                    self._local_state[user_id] = remote_state
                elif remote_state.version == local_state.version:
                    # 版本相同，使用更大的消耗值 (保守策略)
                    if remote_state.consumed_budget > local_state.consumed_budget:
                        local_state.consumed_budget = remote_state.consumed_budget
    
    def clear_pending_operations(self):
        """清空待同步操作"""
        with self._lock:
            self._pending_operations.clear()
    
    def on_sync(self, callback: Callable):
        """注册同步回调"""
        self._sync_callbacks.append(callback)
    
    def start_sync(self):
        """启动同步线程"""
        if self._sync_thread is not None:
            return
        
        self._stop_sync = False
        
        def sync_loop():
            while not self._stop_sync:
                # 触发同步回调
                for callback in self._sync_callbacks:
                    try:
                        callback(self.get_pending_operations())
                    except Exception:
                        pass
                
                time.sleep(self.sync_interval)
        
        self._sync_thread = Thread(target=sync_loop, daemon=True)
        self._sync_thread.start()
    
    def stop_sync(self):
        """停止同步线程"""
        self._stop_sync = True
        if self._sync_thread:
            self._sync_thread.join(timeout=2)
            self._sync_thread = None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "instance_id": self.instance_id,
                "users_tracked": len(self._local_state),
                "pending_operations": len(self._pending_operations),
                "active_locks": len(self._locks),
            }
