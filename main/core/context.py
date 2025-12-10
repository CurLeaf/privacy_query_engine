"""
QueryContext - 查询上下文
用于存储查询执行过程中的上下文信息
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class QueryContext:
    """查询上下文"""
    
    # 用户信息
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    
    # 查询元信息
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 隐私预算(用于后续版本)
    privacy_budget: Optional[float] = None
    
    # 扩展属性
    extra: Dict[str, Any] = field(default_factory=dict)

