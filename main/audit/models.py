"""
Audit Data Models (v3.0)

审计系统的数据模型定义。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json


class EventType(Enum):
    """审计事件类型"""
    QUERY_SUBMITTED = "query_submitted"
    QUERY_ANALYZED = "query_analyzed"
    PRIVACY_APPLIED = "privacy_applied"
    QUERY_REJECTED = "query_rejected"
    BUDGET_CONSUMED = "budget_consumed"
    BUDGET_RESET = "budget_reset"
    CONFIG_CHANGED = "config_changed"
    SYSTEM_ERROR = "system_error"


class PrivacyMethod(Enum):
    """隐私保护方法"""
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    DEIDENTIFICATION = "deidentification"
    K_ANONYMITY = "k_anonymity"
    L_DIVERSITY = "l_diversity"
    NONE = "none"


@dataclass
class QueryEvent:
    """查询事件记录"""
    query_id: str
    user_id: str
    original_sql: str
    timestamp: datetime = field(default_factory=datetime.now)
    tables_accessed: List[str] = field(default_factory=list)
    columns_accessed: List[str] = field(default_factory=list)
    query_type: str = "UNKNOWN"
    is_aggregation: bool = False
    has_joins: bool = False
    has_subqueries: bool = False
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "user_id": self.user_id,
            "original_sql": self.original_sql,
            "timestamp": self.timestamp.isoformat(),
            "tables_accessed": self.tables_accessed,
            "columns_accessed": self.columns_accessed,
            "query_type": self.query_type,
            "is_aggregation": self.is_aggregation,
            "has_joins": self.has_joins,
            "has_subqueries": self.has_subqueries,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class PrivacyEvent:
    """隐私保护事件记录"""
    query_id: str
    privacy_method: PrivacyMethod
    epsilon: Optional[float] = None
    delta: Optional[float] = None
    sensitivity: Optional[float] = None
    k_value: Optional[int] = None  # for k-anonymity
    l_value: Optional[int] = None  # for l-diversity
    noise_added: Optional[float] = None
    columns_protected: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "privacy_method": self.privacy_method.value,
            "epsilon": self.epsilon,
            "delta": self.delta,
            "sensitivity": self.sensitivity,
            "k_value": self.k_value,
            "l_value": self.l_value,
            "noise_added": self.noise_added,
            "columns_protected": self.columns_protected,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    entry_id: str
    event_type: EventType
    timestamp: datetime
    user_id: str
    query_event: Optional[QueryEvent] = None
    privacy_event: Optional[PrivacyEvent] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    
    def __post_init__(self):
        """计算条目哈希以实现防篡改"""
        if self.entry_hash is None:
            self.entry_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """计算条目的哈希值"""
        content = {
            "entry_id": self.entry_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "query_event": self.query_event.to_dict() if self.query_event else None,
            "privacy_event": self.privacy_event.to_dict() if self.privacy_event else None,
            "rejection_reason": self.rejection_reason,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """验证条目完整性"""
        return self.entry_hash == self._calculate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "query_event": self.query_event.to_dict() if self.query_event else None,
            "privacy_event": self.privacy_event.to_dict() if self.privacy_event else None,
            "rejection_reason": self.rejection_reason,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


@dataclass
class AuditFilter:
    """审计日志过滤器"""
    user_id: Optional[str] = None
    event_types: Optional[List[EventType]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    query_id: Optional[str] = None
    privacy_method: Optional[PrivacyMethod] = None
    include_rejected: bool = True
    limit: int = 100
    offset: int = 0
    
    def matches(self, entry: AuditLogEntry) -> bool:
        """检查条目是否匹配过滤条件"""
        if self.user_id and entry.user_id != self.user_id:
            return False
        if self.event_types and entry.event_type not in self.event_types:
            return False
        if self.start_time and entry.timestamp < self.start_time:
            return False
        if self.end_time and entry.timestamp > self.end_time:
            return False
        if self.query_id:
            if entry.query_event and entry.query_event.query_id != self.query_id:
                return False
            if entry.privacy_event and entry.privacy_event.query_id != self.query_id:
                return False
        if self.privacy_method:
            if entry.privacy_event and entry.privacy_event.privacy_method != self.privacy_method:
                return False
        if not self.include_rejected and entry.event_type == EventType.QUERY_REJECTED:
            return False
        return True
