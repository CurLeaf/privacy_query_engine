"""
Tests for Audit Logger (v3.0)
"""
import pytest
from datetime import datetime, timedelta

from main.audit import (
    AuditLogger,
    AuditFilter,
    EventType,
    PrivacyMethod,
)


class TestAuditLogger:
    """审计日志记录器测试"""
    
    def setup_method(self):
        """每个测试前创建新的logger"""
        self.logger = AuditLogger()
    
    def test_log_query_submitted(self):
        """测试记录查询提交事件"""
        entry = self.logger.log_query_submitted(
            query_id="q1",
            user_id="user1",
            original_sql="SELECT COUNT(*) FROM users",
            tables=["users"],
            columns=["*"],
            query_type="SELECT",
            is_aggregation=True,
        )
        
        assert entry.event_type == EventType.QUERY_SUBMITTED
        assert entry.user_id == "user1"
        assert entry.query_event is not None
        assert entry.query_event.query_id == "q1"
        assert entry.query_event.original_sql == "SELECT COUNT(*) FROM users"
        assert entry.query_event.is_aggregation is True
    
    def test_log_privacy_applied(self):
        """测试记录隐私保护应用事件"""
        entry = self.logger.log_privacy_applied(
            query_id="q1",
            user_id="user1",
            privacy_method=PrivacyMethod.DIFFERENTIAL_PRIVACY,
            epsilon=0.1,
            delta=1e-5,
            sensitivity=1.0,
            noise_added=5.5,
            columns_protected=["count"],
        )
        
        assert entry.event_type == EventType.PRIVACY_APPLIED
        assert entry.privacy_event is not None
        assert entry.privacy_event.epsilon == 0.1
        assert entry.privacy_event.delta == 1e-5
        assert entry.privacy_event.noise_added == 5.5
    
    def test_log_query_rejected(self):
        """测试记录查询拒绝事件"""
        entry = self.logger.log_query_rejected(
            query_id="q1",
            user_id="user1",
            original_sql="SELECT * FROM users",
            rejection_reason="Insufficient privacy budget",
        )
        
        assert entry.event_type == EventType.QUERY_REJECTED
        assert entry.rejection_reason == "Insufficient privacy budget"
    
    def test_log_budget_consumed(self):
        """测试记录预算消耗事件"""
        entry = self.logger.log_budget_consumed(
            user_id="user1",
            query_id="q1",
            epsilon_consumed=0.1,
            remaining_budget=0.9,
        )
        
        assert entry.event_type == EventType.BUDGET_CONSUMED
        assert entry.metadata["epsilon_consumed"] == 0.1
        assert entry.metadata["remaining_budget"] == 0.9


class TestAuditFilter:
    """审计日志过滤测试"""
    
    def setup_method(self):
        self.logger = AuditLogger()
        # 创建测试数据
        self.logger.log_query_submitted(
            query_id="q1", user_id="user1", original_sql="SELECT 1"
        )
        self.logger.log_privacy_applied(
            query_id="q1", user_id="user1",
            privacy_method=PrivacyMethod.DIFFERENTIAL_PRIVACY,
            epsilon=0.1,
        )
        self.logger.log_query_submitted(
            query_id="q2", user_id="user2", original_sql="SELECT 2"
        )
        self.logger.log_query_rejected(
            query_id="q3", user_id="user1", original_sql="SELECT 3",
            rejection_reason="Budget exceeded",
        )
    
    def test_filter_by_user(self):
        """测试按用户过滤"""
        entries = self.logger.get_logs_by_user("user1")
        assert len(entries) == 3
        assert all(e.user_id == "user1" for e in entries)
    
    def test_filter_by_event_type(self):
        """测试按事件类型过滤"""
        filter_criteria = AuditFilter(
            event_types=[EventType.QUERY_SUBMITTED]
        )
        entries = self.logger.filter_logs(filter_criteria)
        assert len(entries) == 2
        assert all(e.event_type == EventType.QUERY_SUBMITTED for e in entries)
    
    def test_filter_exclude_rejected(self):
        """测试排除拒绝的查询"""
        filter_criteria = AuditFilter(include_rejected=False)
        entries = self.logger.filter_logs(filter_criteria)
        assert all(e.event_type != EventType.QUERY_REJECTED for e in entries)


class TestAuditChainIntegrity:
    """审计日志链完整性测试"""
    
    def test_chain_integrity(self):
        """测试日志链完整性验证"""
        logger = AuditLogger()
        
        # 添加多个条目
        logger.log_query_submitted(
            query_id="q1", user_id="user1", original_sql="SELECT 1"
        )
        logger.log_query_submitted(
            query_id="q2", user_id="user1", original_sql="SELECT 2"
        )
        logger.log_query_submitted(
            query_id="q3", user_id="user1", original_sql="SELECT 3"
        )
        
        # 验证链完整性
        assert logger.verify_chain_integrity() is True
    
    def test_entry_integrity(self):
        """测试单个条目完整性"""
        logger = AuditLogger()
        entry = logger.log_query_submitted(
            query_id="q1", user_id="user1", original_sql="SELECT 1"
        )
        
        assert entry.verify_integrity() is True


class TestAuditExport:
    """审计日志导出测试"""
    
    def setup_method(self):
        self.logger = AuditLogger()
        self.logger.log_query_submitted(
            query_id="q1", user_id="user1", original_sql="SELECT 1"
        )
        self.logger.log_privacy_applied(
            query_id="q1", user_id="user1",
            privacy_method=PrivacyMethod.DIFFERENTIAL_PRIVACY,
            epsilon=0.1,
        )
    
    def test_export_json(self):
        """测试JSON导出"""
        json_output = self.logger.export_json()
        assert "export_timestamp" in json_output
        assert "entries" in json_output
        assert "q1" in json_output
    
    def test_export_csv(self):
        """测试CSV导出"""
        csv_output = self.logger.export_csv()
        lines = csv_output.split("\n")
        assert len(lines) == 3  # header + 2 entries
        assert "entry_id" in lines[0]
        assert "query_submitted" in lines[1]
    
    def test_get_statistics(self):
        """测试统计信息"""
        stats = self.logger.get_statistics()
        assert stats["total_entries"] == 2
        assert "query_submitted" in stats["by_event_type"]
        assert "privacy_applied" in stats["by_event_type"]
