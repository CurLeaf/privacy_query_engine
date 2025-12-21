"""
Privacy Budget Models - 隐私预算数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional
from enum import Enum


class ResetFrequency(Enum):
    """预算重置频率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


@dataclass
class ResetSchedule:
    """预算重置计划"""
    frequency: ResetFrequency = ResetFrequency.DAILY
    reset_time: time = field(default_factory=lambda: time(0, 0, 0))
    timezone: str = "UTC"
    
    def to_dict(self) -> dict:
        return {
            "frequency": self.frequency.value,
            "reset_time": self.reset_time.isoformat(),
            "timezone": self.timezone
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ResetSchedule":
        return cls(
            frequency=ResetFrequency(data.get("frequency", "daily")),
            reset_time=time.fromisoformat(data.get("reset_time", "00:00:00")),
            timezone=data.get("timezone", "UTC")
        )


@dataclass
class BudgetAccount:
    """隐私预算账户"""
    user_id: str
    total_budget: float  # 总预算 (epsilon)
    consumed_budget: float = 0.0  # 已消耗预算
    reset_schedule: ResetSchedule = field(default_factory=ResetSchedule)
    last_reset: Optional[datetime] = None
    role: str = "default"  # 用户角色，用于角色基础的预算分配
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def remaining_budget(self) -> float:
        """剩余预算"""
        return max(0.0, self.total_budget - self.consumed_budget)
    
    @property
    def is_exhausted(self) -> bool:
        """预算是否耗尽"""
        return self.remaining_budget <= 0
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "total_budget": self.total_budget,
            "consumed_budget": self.consumed_budget,
            "remaining_budget": self.remaining_budget,
            "reset_schedule": self.reset_schedule.to_dict(),
            "last_reset": self.last_reset.isoformat() if self.last_reset else None,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class BudgetTransaction:
    """预算交易记录"""
    transaction_id: str
    user_id: str
    query_id: str
    epsilon_consumed: float
    timestamp: datetime = field(default_factory=datetime.now)
    query_hash: str = ""
    privacy_mechanism: str = "laplace"  # laplace, gaussian, etc.
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "query_id": self.query_id,
            "epsilon_consumed": self.epsilon_consumed,
            "timestamp": self.timestamp.isoformat(),
            "query_hash": self.query_hash,
            "privacy_mechanism": self.privacy_mechanism,
            "description": self.description
        }


@dataclass
class BudgetCheckResult:
    """预算检查结果"""
    allowed: bool
    remaining_budget: float
    requested_budget: float
    message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "remaining_budget": self.remaining_budget,
            "requested_budget": self.requested_budget,
            "message": self.message
        }
