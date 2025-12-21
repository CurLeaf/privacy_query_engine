"""
Distributed Coordinator (v3.0)

分布式协调器，管理服务实例注册、发现和健康检查。
"""
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from threading import Lock, Thread


class InstanceStatus(Enum):
    """实例状态"""
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    STOPPED = "stopped"


@dataclass
class ServiceInstance:
    """服务实例"""
    instance_id: str
    host: str
    port: int
    status: InstanceStatus = InstanceStatus.STARTING
    weight: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    health_check_failures: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "weight": self.weight,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "health_check_failures": self.health_check_failures,
        }
    
    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


class DistributedCoordinator:
    """
    分布式协调器
    
    提供:
    - 服务实例注册和发现
    - 健康检查
    - 自动故障转移
    - 零停机扩展支持
    """
    
    def __init__(
        self,
        heartbeat_interval_seconds: float = 5.0,
        health_check_timeout_seconds: float = 10.0,
        max_health_check_failures: int = 3,
    ):
        """
        初始化分布式协调器
        
        Args:
            heartbeat_interval_seconds: 心跳间隔
            health_check_timeout_seconds: 健康检查超时
            max_health_check_failures: 最大健康检查失败次数
        """
        self._instances: Dict[str, ServiceInstance] = {}
        self._lock = Lock()
        self.heartbeat_interval = heartbeat_interval_seconds
        self.health_check_timeout = health_check_timeout_seconds
        self.max_health_check_failures = max_health_check_failures
        
        self._health_check_thread: Optional[Thread] = None
        self._stop_health_check = False
        self._health_check_callbacks: List[Callable] = []
        self._instance_change_callbacks: List[Callable] = []
    
    def register(
        self,
        host: str,
        port: int,
        weight: int = 100,
        metadata: Dict[str, Any] = None,
    ) -> ServiceInstance:
        """
        注册服务实例
        
        Args:
            host: 主机地址
            port: 端口
            weight: 权重
            metadata: 元数据
            
        Returns:
            注册的服务实例
        """
        instance_id = f"instance_{uuid.uuid4().hex[:12]}"
        
        instance = ServiceInstance(
            instance_id=instance_id,
            host=host,
            port=port,
            weight=weight,
            metadata=metadata or {},
            status=InstanceStatus.HEALTHY,
        )
        
        with self._lock:
            self._instances[instance_id] = instance
        
        # 触发实例变更回调
        self._notify_instance_change("register", instance)
        
        return instance
    
    def deregister(self, instance_id: str) -> bool:
        """注销服务实例"""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            instance = self._instances.pop(instance_id)
            instance.status = InstanceStatus.STOPPED
        
        self._notify_instance_change("deregister", instance)
        return True
    
    def heartbeat(self, instance_id: str) -> bool:
        """更新实例心跳"""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            instance = self._instances[instance_id]
            instance.last_heartbeat = datetime.now()
            instance.health_check_failures = 0
            
            if instance.status == InstanceStatus.UNHEALTHY:
                instance.status = InstanceStatus.HEALTHY
                self._notify_instance_change("recovered", instance)
            
            return True
    
    def get_instance(self, instance_id: str) -> Optional[ServiceInstance]:
        """获取服务实例"""
        with self._lock:
            return self._instances.get(instance_id)
    
    def get_healthy_instances(self) -> List[ServiceInstance]:
        """获取所有健康的实例"""
        with self._lock:
            return [
                inst for inst in self._instances.values()
                if inst.status == InstanceStatus.HEALTHY
            ]
    
    def get_all_instances(self) -> List[ServiceInstance]:
        """获取所有实例"""
        with self._lock:
            return list(self._instances.values())
    
    def set_instance_status(self, instance_id: str, status: InstanceStatus) -> bool:
        """设置实例状态"""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            old_status = self._instances[instance_id].status
            self._instances[instance_id].status = status
            
            if old_status != status:
                self._notify_instance_change("status_change", self._instances[instance_id])
            
            return True
    
    def drain_instance(self, instance_id: str) -> bool:
        """
        排空实例 (用于优雅关闭)
        
        将实例标记为draining状态，不再接收新请求
        """
        return self.set_instance_status(instance_id, InstanceStatus.DRAINING)
    
    def start_health_check(self):
        """启动健康检查"""
        if self._health_check_thread is not None:
            return
        
        self._stop_health_check = False
        
        def check_loop():
            while not self._stop_health_check:
                self._perform_health_check()
                time.sleep(self.heartbeat_interval)
        
        self._health_check_thread = Thread(target=check_loop, daemon=True)
        self._health_check_thread.start()
    
    def stop_health_check(self):
        """停止健康检查"""
        self._stop_health_check = True
        if self._health_check_thread:
            self._health_check_thread.join(timeout=2)
            self._health_check_thread = None
    
    def _perform_health_check(self):
        """执行健康检查"""
        now = datetime.now()
        
        with self._lock:
            for instance in self._instances.values():
                if instance.status == InstanceStatus.STOPPED:
                    continue
                
                # 检查心跳超时
                elapsed = (now - instance.last_heartbeat).total_seconds()
                
                if elapsed > self.health_check_timeout:
                    instance.health_check_failures += 1
                    
                    if instance.health_check_failures >= self.max_health_check_failures:
                        if instance.status != InstanceStatus.UNHEALTHY:
                            instance.status = InstanceStatus.UNHEALTHY
                            self._notify_instance_change("unhealthy", instance)
                            
                            # 触发健康检查回调
                            for callback in self._health_check_callbacks:
                                try:
                                    callback(instance, "timeout")
                                except Exception:
                                    pass
    
    def _notify_instance_change(self, event: str, instance: ServiceInstance):
        """通知实例变更"""
        for callback in self._instance_change_callbacks:
            try:
                callback(event, instance)
            except Exception:
                pass
    
    def on_health_check_failure(self, callback: Callable):
        """注册健康检查失败回调"""
        self._health_check_callbacks.append(callback)
    
    def on_instance_change(self, callback: Callable):
        """注册实例变更回调"""
        self._instance_change_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            status_counts = {}
            for inst in self._instances.values():
                status = inst.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_instances": len(self._instances),
                "healthy_instances": status_counts.get("healthy", 0),
                "unhealthy_instances": status_counts.get("unhealthy", 0),
                "draining_instances": status_counts.get("draining", 0),
                "status_breakdown": status_counts,
            }
    
    def get_health_endpoint(self) -> Dict[str, Any]:
        """获取健康端点响应"""
        stats = self.get_statistics()
        healthy = stats["healthy_instances"] > 0
        
        return {
            "status": "healthy" if healthy else "unhealthy",
            "instances": stats,
            "timestamp": datetime.now().isoformat(),
        }
