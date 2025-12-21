"""
Audit Logger (v3.0)

全面的审计日志记录器，支持防篡改日志和合规性导出。
"""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from threading import Lock

from .models import (
    AuditLogEntry, 
    AuditFilter, 
    EventType, 
    QueryEvent, 
    PrivacyEvent,
    PrivacyMethod,
)


class AuditLogger:
    """
    审计日志记录器
    
    提供:
    - 全面的查询和隐私事件日志记录
    - 防篡改日志链
    - 日志过滤和搜索
    - 合规性导出格式
    """
    
    def __init__(self, max_entries: int = 10000):
        """
        初始化审计日志记录器
        
        Args:
            max_entries: 内存中保留的最大条目数
        """
        self._entries: List[AuditLogEntry] = []
        self._max_entries = max_entries
        self._lock = Lock()
        self._last_hash: Optional[str] = None
    
    def _generate_entry_id(self) -> str:
        """生成唯一的条目ID"""
        return f"audit_{uuid.uuid4().hex[:16]}"
    
    def _add_entry(self, entry: AuditLogEntry) -> AuditLogEntry:
        """添加条目到日志"""
        with self._lock:
            # 设置前一个哈希以形成链
            entry.previous_hash = self._last_hash
            entry.entry_hash = entry._calculate_hash()
            self._last_hash = entry.entry_hash
            
            self._entries.append(entry)
            
            # 如果超过最大条目数，移除最旧的
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]
        
        return entry
    
    def log_query_submitted(
        self,
        query_id: str,
        user_id: str,
        original_sql: str,
        tables: List[str] = None,
        columns: List[str] = None,
        query_type: str = "UNKNOWN",
        is_aggregation: bool = False,
        has_joins: bool = False,
        has_subqueries: bool = False,
        metadata: Dict[str, Any] = None,
    ) -> AuditLogEntry:
        """记录查询提交事件"""
        query_event = QueryEvent(
            query_id=query_id,
            user_id=user_id,
            original_sql=original_sql,
            tables_accessed=tables or [],
            columns_accessed=columns or [],
            query_type=query_type,
            is_aggregation=is_aggregation,
            has_joins=has_joins,
            has_subqueries=has_subqueries,
        )
        
        entry = AuditLogEntry(
            entry_id=self._generate_entry_id(),
            event_type=EventType.QUERY_SUBMITTED,
            timestamp=datetime.now(),
            user_id=user_id,
            query_event=query_event,
            metadata=metadata or {},
        )
        
        return self._add_entry(entry)
    
    def log_privacy_applied(
        self,
        query_id: str,
        user_id: str,
        privacy_method: PrivacyMethod,
        epsilon: float = None,
        delta: float = None,
        sensitivity: float = None,
        k_value: int = None,
        l_value: int = None,
        noise_added: float = None,
        columns_protected: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> AuditLogEntry:
        """记录隐私保护应用事件"""
        privacy_event = PrivacyEvent(
            query_id=query_id,
            privacy_method=privacy_method,
            epsilon=epsilon,
            delta=delta,
            sensitivity=sensitivity,
            k_value=k_value,
            l_value=l_value,
            noise_added=noise_added,
            columns_protected=columns_protected or [],
        )
        
        entry = AuditLogEntry(
            entry_id=self._generate_entry_id(),
            event_type=EventType.PRIVACY_APPLIED,
            timestamp=datetime.now(),
            user_id=user_id,
            privacy_event=privacy_event,
            metadata=metadata or {},
        )
        
        return self._add_entry(entry)
    
    def log_query_rejected(
        self,
        query_id: str,
        user_id: str,
        original_sql: str,
        rejection_reason: str,
        metadata: Dict[str, Any] = None,
    ) -> AuditLogEntry:
        """记录查询拒绝事件"""
        query_event = QueryEvent(
            query_id=query_id,
            user_id=user_id,
            original_sql=original_sql,
        )
        
        entry = AuditLogEntry(
            entry_id=self._generate_entry_id(),
            event_type=EventType.QUERY_REJECTED,
            timestamp=datetime.now(),
            user_id=user_id,
            query_event=query_event,
            rejection_reason=rejection_reason,
            metadata=metadata or {},
        )
        
        return self._add_entry(entry)
    
    def log_budget_consumed(
        self,
        user_id: str,
        query_id: str,
        epsilon_consumed: float,
        remaining_budget: float,
        metadata: Dict[str, Any] = None,
    ) -> AuditLogEntry:
        """记录预算消耗事件"""
        entry = AuditLogEntry(
            entry_id=self._generate_entry_id(),
            event_type=EventType.BUDGET_CONSUMED,
            timestamp=datetime.now(),
            user_id=user_id,
            metadata={
                "query_id": query_id,
                "epsilon_consumed": epsilon_consumed,
                "remaining_budget": remaining_budget,
                **(metadata or {}),
            },
        )
        
        return self._add_entry(entry)
    
    def log_budget_reset(
        self,
        user_id: str,
        new_budget: float,
        reset_reason: str = "scheduled",
        metadata: Dict[str, Any] = None,
    ) -> AuditLogEntry:
        """记录预算重置事件"""
        entry = AuditLogEntry(
            entry_id=self._generate_entry_id(),
            event_type=EventType.BUDGET_RESET,
            timestamp=datetime.now(),
            user_id=user_id,
            metadata={
                "new_budget": new_budget,
                "reset_reason": reset_reason,
                **(metadata or {}),
            },
        )
        
        return self._add_entry(entry)
    
    def log_config_changed(
        self,
        user_id: str,
        config_type: str,
        changes: Dict[str, Any],
        metadata: Dict[str, Any] = None,
    ) -> AuditLogEntry:
        """记录配置变更事件"""
        entry = AuditLogEntry(
            entry_id=self._generate_entry_id(),
            event_type=EventType.CONFIG_CHANGED,
            timestamp=datetime.now(),
            user_id=user_id,
            metadata={
                "config_type": config_type,
                "changes": changes,
                **(metadata or {}),
            },
        )
        
        return self._add_entry(entry)
    
    def log_system_error(
        self,
        user_id: str,
        error_type: str,
        error_message: str,
        query_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> AuditLogEntry:
        """记录系统错误事件"""
        entry = AuditLogEntry(
            entry_id=self._generate_entry_id(),
            event_type=EventType.SYSTEM_ERROR,
            timestamp=datetime.now(),
            user_id=user_id,
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "query_id": query_id,
                **(metadata or {}),
            },
        )
        
        return self._add_entry(entry)
    
    def filter_logs(self, filter_criteria: AuditFilter) -> List[AuditLogEntry]:
        """根据条件过滤日志"""
        with self._lock:
            filtered = [e for e in self._entries if filter_criteria.matches(e)]
            
            # 应用分页
            start = filter_criteria.offset
            end = start + filter_criteria.limit
            return filtered[start:end]
    
    def get_logs_by_user(self, user_id: str, limit: int = 100) -> List[AuditLogEntry]:
        """获取指定用户的日志"""
        filter_criteria = AuditFilter(user_id=user_id, limit=limit)
        return self.filter_logs(filter_criteria)
    
    def get_logs_by_query(self, query_id: str) -> List[AuditLogEntry]:
        """获取指定查询的所有日志"""
        filter_criteria = AuditFilter(query_id=query_id, limit=1000)
        return self.filter_logs(filter_criteria)
    
    def get_logs_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 100,
    ) -> List[AuditLogEntry]:
        """获取指定时间范围的日志"""
        filter_criteria = AuditFilter(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        return self.filter_logs(filter_criteria)
    
    def verify_chain_integrity(self) -> bool:
        """验证日志链的完整性"""
        with self._lock:
            if not self._entries:
                return True
            
            # 验证第一个条目
            if not self._entries[0].verify_integrity():
                return False
            
            # 验证链
            for i in range(1, len(self._entries)):
                current = self._entries[i]
                previous = self._entries[i - 1]
                
                # 验证当前条目完整性
                if not current.verify_integrity():
                    return False
                
                # 验证链接
                if current.previous_hash != previous.entry_hash:
                    return False
            
            return True
    
    def export_json(self, filter_criteria: AuditFilter = None) -> str:
        """导出为JSON格式"""
        if filter_criteria:
            entries = self.filter_logs(filter_criteria)
        else:
            with self._lock:
                entries = list(self._entries)
        
        return json.dumps(
            {
                "export_timestamp": datetime.now().isoformat(),
                "total_entries": len(entries),
                "entries": [e.to_dict() for e in entries],
            },
            indent=2,
            ensure_ascii=False,
        )
    
    def export_csv(self, filter_criteria: AuditFilter = None) -> str:
        """导出为CSV格式（合规性报告）"""
        if filter_criteria:
            entries = self.filter_logs(filter_criteria)
        else:
            with self._lock:
                entries = list(self._entries)
        
        lines = [
            "entry_id,event_type,timestamp,user_id,query_id,privacy_method,epsilon,rejection_reason"
        ]
        
        for entry in entries:
            query_id = ""
            privacy_method = ""
            epsilon = ""
            
            if entry.query_event:
                query_id = entry.query_event.query_id
            if entry.privacy_event:
                query_id = entry.privacy_event.query_id
                privacy_method = entry.privacy_event.privacy_method.value
                epsilon = str(entry.privacy_event.epsilon) if entry.privacy_event.epsilon else ""
            
            rejection = entry.rejection_reason or ""
            # 转义CSV特殊字符
            rejection = rejection.replace('"', '""')
            if ',' in rejection or '"' in rejection:
                rejection = f'"{rejection}"'
            
            lines.append(
                f"{entry.entry_id},{entry.event_type.value},{entry.timestamp.isoformat()},"
                f"{entry.user_id},{query_id},{privacy_method},{epsilon},{rejection}"
            )
        
        return "\n".join(lines)
    
    def export_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        format: str = "json",
    ) -> str:
        """
        导出合规性报告
        
        Args:
            start_time: 报告开始时间
            end_time: 报告结束时间
            format: 导出格式 (json/csv)
        """
        filter_criteria = AuditFilter(
            start_time=start_time,
            end_time=end_time,
            limit=100000,  # 合规报告需要完整数据
        )
        
        if format == "csv":
            return self.export_csv(filter_criteria)
        return self.export_json(filter_criteria)
    
    def get_statistics(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> Dict[str, Any]:
        """获取审计统计信息"""
        filter_criteria = AuditFilter(
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )
        entries = self.filter_logs(filter_criteria)
        
        stats = {
            "total_entries": len(entries),
            "by_event_type": {},
            "by_user": {},
            "by_privacy_method": {},
            "rejected_queries": 0,
            "total_epsilon_consumed": 0.0,
        }
        
        for entry in entries:
            # 按事件类型统计
            event_type = entry.event_type.value
            stats["by_event_type"][event_type] = stats["by_event_type"].get(event_type, 0) + 1
            
            # 按用户统计
            stats["by_user"][entry.user_id] = stats["by_user"].get(entry.user_id, 0) + 1
            
            # 统计拒绝的查询
            if entry.event_type == EventType.QUERY_REJECTED:
                stats["rejected_queries"] += 1
            
            # 按隐私方法统计
            if entry.privacy_event:
                method = entry.privacy_event.privacy_method.value
                stats["by_privacy_method"][method] = stats["by_privacy_method"].get(method, 0) + 1
                
                if entry.privacy_event.epsilon:
                    stats["total_epsilon_consumed"] += entry.privacy_event.epsilon
        
        return stats
    
    def clear(self):
        """清空日志（仅用于测试）"""
        with self._lock:
            self._entries.clear()
            self._last_hash = None
