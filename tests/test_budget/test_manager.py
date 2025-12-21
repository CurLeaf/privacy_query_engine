"""
Privacy Budget Manager 单元测试
"""
import pytest
from datetime import datetime, timedelta

from main.budget import (
    PrivacyBudgetManager,
    BudgetAccount,
    BudgetTransaction,
    ResetSchedule,
    BudgetCheckResult
)
from main.budget.models import ResetFrequency


class TestBudgetModels:
    """预算模型测试"""
    
    def test_budget_account_creation(self):
        """测试预算账户创建"""
        account = BudgetAccount(
            user_id="user1",
            total_budget=5.0
        )
        
        assert account.user_id == "user1"
        assert account.total_budget == 5.0
        assert account.consumed_budget == 0.0
        assert account.remaining_budget == 5.0
        assert not account.is_exhausted
    
    def test_budget_account_remaining(self):
        """测试剩余预算计算"""
        account = BudgetAccount(
            user_id="user1",
            total_budget=5.0,
            consumed_budget=3.0
        )
        
        assert account.remaining_budget == 2.0
        assert not account.is_exhausted
    
    def test_budget_account_exhausted(self):
        """测试预算耗尽"""
        account = BudgetAccount(
            user_id="user1",
            total_budget=5.0,
            consumed_budget=5.0
        )
        
        assert account.remaining_budget == 0.0
        assert account.is_exhausted
    
    def test_reset_schedule_creation(self):
        """测试重置计划创建"""
        schedule = ResetSchedule(
            frequency=ResetFrequency.WEEKLY
        )
        
        assert schedule.frequency == ResetFrequency.WEEKLY
        assert schedule.timezone == "UTC"
    
    def test_budget_check_result(self):
        """测试预算检查结果"""
        result = BudgetCheckResult(
            allowed=True,
            remaining_budget=5.0,
            requested_budget=1.0,
            message="OK"
        )
        
        assert result.allowed
        assert result.remaining_budget == 5.0


class TestPrivacyBudgetManager:
    """隐私预算管理器测试"""
    
    def setup_method(self):
        self.manager = PrivacyBudgetManager(default_budget=5.0)
    
    def test_get_or_create_account(self):
        """测试获取或创建账户"""
        account = self.manager.get_or_create_account("user1")
        
        assert account.user_id == "user1"
        assert account.total_budget == 5.0
        
        # 再次获取应该返回同一个账户
        account2 = self.manager.get_or_create_account("user1")
        assert account2 is account
    
    def test_role_based_budget(self):
        """测试基于角色的预算"""
        manager = PrivacyBudgetManager(
            role_budgets={"admin": 10.0, "analyst": 5.0, "default": 1.0}
        )
        
        admin_account = manager.get_or_create_account("admin1", role="admin")
        analyst_account = manager.get_or_create_account("analyst1", role="analyst")
        default_account = manager.get_or_create_account("user1", role="default")
        
        assert admin_account.total_budget == 10.0
        assert analyst_account.total_budget == 5.0
        assert default_account.total_budget == 1.0
    
    def test_check_budget_sufficient(self):
        """测试预算充足时的检查"""
        result = self.manager.check_budget("user1", 1.0)
        
        assert result.allowed
        assert result.remaining_budget == 5.0
        assert result.requested_budget == 1.0
    
    def test_check_budget_insufficient(self):
        """测试预算不足时的检查"""
        result = self.manager.check_budget("user1", 10.0)
        
        assert not result.allowed
        assert result.remaining_budget == 5.0
        assert result.requested_budget == 10.0
    
    def test_consume_budget_success(self):
        """测试成功消耗预算"""
        success = self.manager.consume_budget("user1", 2.0)
        
        assert success
        assert self.manager.get_remaining_budget("user1") == 3.0
    
    def test_consume_budget_failure(self):
        """测试预算不足时消耗失败"""
        success = self.manager.consume_budget("user1", 10.0)
        
        assert not success
        assert self.manager.get_remaining_budget("user1") == 5.0
    
    def test_consume_budget_multiple(self):
        """测试多次消耗预算"""
        self.manager.consume_budget("user1", 1.0)
        self.manager.consume_budget("user1", 2.0)
        
        assert self.manager.get_remaining_budget("user1") == 2.0
    
    def test_get_budget_status(self):
        """测试获取预算状态"""
        self.manager.consume_budget("user1", 2.0)
        status = self.manager.get_budget_status("user1")
        
        assert status["user_id"] == "user1"
        assert status["total_budget"] == 5.0
        assert status["consumed_budget"] == 2.0
        assert status["remaining_budget"] == 3.0
        assert not status["is_exhausted"]
    
    def test_get_budget_history(self):
        """测试获取预算历史"""
        self.manager.consume_budget("user1", 1.0, query_id="q1")
        self.manager.consume_budget("user1", 2.0, query_id="q2")
        
        history = self.manager.get_budget_history("user1")
        
        assert len(history) == 2
        assert history[0].query_id == "q2"  # 最新的在前
        assert history[1].query_id == "q1"
    
    def test_reset_budget(self):
        """测试重置预算"""
        self.manager.consume_budget("user1", 3.0)
        assert self.manager.get_remaining_budget("user1") == 2.0
        
        self.manager.reset_budget("user1")
        assert self.manager.get_remaining_budget("user1") == 5.0
    
    def test_set_budget(self):
        """测试设置预算"""
        self.manager.set_budget("user1", 10.0)
        
        assert self.manager.get_remaining_budget("user1") == 10.0
    
    def test_atomic_budget_update(self):
        """测试原子预算更新"""
        # 消耗预算
        self.manager.consume_budget("user1", 2.0)
        
        # 检查预算状态一致
        status = self.manager.get_budget_status("user1")
        assert status["consumed_budget"] == 2.0
        assert status["remaining_budget"] == 3.0
        
        # 再次消耗
        self.manager.consume_budget("user1", 1.5)
        
        status = self.manager.get_budget_status("user1")
        assert status["consumed_budget"] == 3.5
        assert status["remaining_budget"] == 1.5


class TestBudgetResetSchedule:
    """预算重置计划测试"""
    
    def test_daily_reset(self):
        """测试每日重置"""
        manager = PrivacyBudgetManager(
            default_budget=5.0,
            default_reset_schedule=ResetSchedule(frequency=ResetFrequency.DAILY)
        )
        
        # 消耗预算
        manager.consume_budget("user1", 3.0)
        assert manager.get_remaining_budget("user1") == 2.0
        
        # 模拟时间过去一天
        account = manager._accounts["user1"]
        account.last_reset = datetime.now() - timedelta(days=2)
        
        # 检查预算应该被重置
        assert manager.get_remaining_budget("user1") == 5.0
    
    def test_never_reset(self):
        """测试永不重置"""
        manager = PrivacyBudgetManager(
            default_budget=5.0,
            default_reset_schedule=ResetSchedule(frequency=ResetFrequency.NEVER)
        )
        
        manager.consume_budget("user1", 3.0)
        
        # 模拟时间过去很久
        account = manager._accounts["user1"]
        account.last_reset = datetime.now() - timedelta(days=365)
        
        # 预算不应该被重置
        assert manager.get_remaining_budget("user1") == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
