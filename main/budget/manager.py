"""
PrivacyBudgetManager - 隐私预算管理器
职责: 跟踪和管理差分隐私预算消耗
"""
import threading
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .models import (
    BudgetAccount,
    BudgetTransaction,
    ResetSchedule,
    ResetFrequency,
    BudgetCheckResult
)


class PrivacyBudgetManager:
    """隐私预算管理器"""
    
    # 默认预算配置
    DEFAULT_BUDGET = 1.0  # 默认epsilon预算
    DEFAULT_ROLE_BUDGETS = {
        "admin": 10.0,
        "analyst": 5.0,
        "default": 1.0
    }
    
    def __init__(
        self,
        default_budget: float = DEFAULT_BUDGET,
        role_budgets: Optional[Dict[str, float]] = None,
        default_reset_schedule: Optional[ResetSchedule] = None
    ):
        """
        初始化预算管理器
        
        Args:
            default_budget: 默认预算
            role_budgets: 角色预算映射
            default_reset_schedule: 默认重置计划
        """
        self._accounts: Dict[str, BudgetAccount] = {}
        self._transactions: Dict[str, List[BudgetTransaction]] = {}
        self._lock = threading.RLock()
        
        self.default_budget = default_budget
        # 使用传入的role_budgets或创建新的，确保default角色使用default_budget
        if role_budgets is not None:
            self.role_budgets = role_budgets.copy()
        else:
            self.role_budgets = self.DEFAULT_ROLE_BUDGETS.copy()
        # 确保default角色使用传入的default_budget
        self.role_budgets["default"] = default_budget
        
        self.default_reset_schedule = default_reset_schedule or ResetSchedule()
    
    def get_or_create_account(
        self,
        user_id: str,
        role: str = "default",
        total_budget: Optional[float] = None
    ) -> BudgetAccount:
        """获取或创建用户预算账户"""
        with self._lock:
            if user_id not in self._accounts:
                # 根据角色确定预算
                if total_budget is None:
                    total_budget = self.role_budgets.get(role, self.default_budget)
                
                account = BudgetAccount(
                    user_id=user_id,
                    total_budget=total_budget,
                    role=role,
                    reset_schedule=ResetSchedule(
                        frequency=self.default_reset_schedule.frequency,
                        reset_time=self.default_reset_schedule.reset_time,
                        timezone=self.default_reset_schedule.timezone
                    )
                )
                self._accounts[user_id] = account
                self._transactions[user_id] = []
            
            return self._accounts[user_id]
    
    def check_budget(self, user_id: str, epsilon: float) -> BudgetCheckResult:
        """
        检查用户是否有足够的预算
        
        Args:
            user_id: 用户ID
            epsilon: 请求的epsilon值
            
        Returns:
            BudgetCheckResult对象
        """
        with self._lock:
            account = self.get_or_create_account(user_id)
            
            # 检查是否需要重置预算
            self._check_and_reset_if_needed(account)
            
            remaining = account.remaining_budget
            allowed = remaining >= epsilon
            
            if allowed:
                message = f"Budget check passed. Remaining: {remaining:.4f}, Requested: {epsilon:.4f}"
            else:
                message = f"Insufficient budget. Remaining: {remaining:.4f}, Requested: {epsilon:.4f}"
            
            return BudgetCheckResult(
                allowed=allowed,
                remaining_budget=remaining,
                requested_budget=epsilon,
                message=message
            )
    
    def consume_budget(
        self,
        user_id: str,
        epsilon: float,
        query_id: Optional[str] = None,
        query_sql: Optional[str] = None,
        privacy_mechanism: str = "laplace"
    ) -> bool:
        """
        消耗用户预算
        
        Args:
            user_id: 用户ID
            epsilon: 消耗的epsilon值
            query_id: 查询ID
            query_sql: 查询SQL（用于生成hash）
            privacy_mechanism: 使用的隐私机制
            
        Returns:
            是否成功消耗预算
        """
        with self._lock:
            account = self.get_or_create_account(user_id)
            
            # 检查是否需要重置预算
            self._check_and_reset_if_needed(account)
            
            # 检查预算是否足够
            if account.remaining_budget < epsilon:
                return False
            
            # 原子更新预算
            account.consumed_budget += epsilon
            account.updated_at = datetime.now()
            
            # 记录交易
            transaction = BudgetTransaction(
                transaction_id=str(uuid.uuid4()),
                user_id=user_id,
                query_id=query_id or str(uuid.uuid4()),
                epsilon_consumed=epsilon,
                query_hash=self._hash_query(query_sql) if query_sql else "",
                privacy_mechanism=privacy_mechanism,
                description=f"Budget consumed: {epsilon:.4f}"
            )
            
            self._transactions[user_id].append(transaction)
            
            return True
    
    def get_remaining_budget(self, user_id: str) -> float:
        """获取用户剩余预算"""
        with self._lock:
            account = self.get_or_create_account(user_id)
            self._check_and_reset_if_needed(account)
            return account.remaining_budget
    
    def get_budget_status(self, user_id: str) -> Dict:
        """获取用户预算状态"""
        with self._lock:
            account = self.get_or_create_account(user_id)
            self._check_and_reset_if_needed(account)
            
            return {
                "user_id": user_id,
                "total_budget": account.total_budget,
                "consumed_budget": account.consumed_budget,
                "remaining_budget": account.remaining_budget,
                "role": account.role,
                "reset_schedule": account.reset_schedule.to_dict(),
                "last_reset": account.last_reset.isoformat() if account.last_reset else None,
                "is_exhausted": account.is_exhausted
            }
    
    def get_budget_history(self, user_id: str, limit: int = 100) -> List[BudgetTransaction]:
        """获取用户预算历史"""
        with self._lock:
            if user_id not in self._transactions:
                return []
            
            transactions = self._transactions[user_id]
            return sorted(transactions, key=lambda t: t.timestamp, reverse=True)[:limit]
    
    def reset_budget(self, user_id: str) -> None:
        """手动重置用户预算"""
        with self._lock:
            account = self.get_or_create_account(user_id)
            account.consumed_budget = 0.0
            account.last_reset = datetime.now()
            account.updated_at = datetime.now()
    
    def set_budget(self, user_id: str, total_budget: float) -> None:
        """设置用户总预算"""
        with self._lock:
            account = self.get_or_create_account(user_id)
            account.total_budget = total_budget
            account.updated_at = datetime.now()
    
    def set_reset_schedule(self, user_id: str, schedule: ResetSchedule) -> None:
        """设置用户预算重置计划"""
        with self._lock:
            account = self.get_or_create_account(user_id)
            account.reset_schedule = schedule
            account.updated_at = datetime.now()
    
    def _check_and_reset_if_needed(self, account: BudgetAccount) -> None:
        """检查并在需要时重置预算"""
        if account.reset_schedule.frequency == ResetFrequency.NEVER:
            return
        
        now = datetime.now()
        
        # 如果从未重置过，设置初始重置时间
        if account.last_reset is None:
            account.last_reset = now
            return
        
        should_reset = False
        
        if account.reset_schedule.frequency == ResetFrequency.DAILY:
            # 每天重置
            if (now - account.last_reset) >= timedelta(days=1):
                should_reset = True
        elif account.reset_schedule.frequency == ResetFrequency.WEEKLY:
            # 每周重置
            if (now - account.last_reset) >= timedelta(weeks=1):
                should_reset = True
        elif account.reset_schedule.frequency == ResetFrequency.MONTHLY:
            # 每月重置（简化为30天）
            if (now - account.last_reset) >= timedelta(days=30):
                should_reset = True
        
        if should_reset:
            account.consumed_budget = 0.0
            account.last_reset = now
            account.updated_at = now
    
    def _hash_query(self, sql: str) -> str:
        """生成查询的hash值"""
        if not sql:
            return ""
        normalized = " ".join(sql.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
