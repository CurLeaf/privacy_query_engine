"""
策略引擎单元测试
"""
import pytest
from main.analyzer import AnalysisResult
from main.policy import PolicyEngine, PolicyDecision


class TestPolicyEngine:
    """PolicyEngine测试类"""
    
    def setup_method(self):
        self.engine = PolicyEngine()
    
    def test_dp_decision_for_aggregation(self):
        """测试聚合查询应返回DP决策"""
        analysis = AnalysisResult(
            tables=["users"],
            aggregations=["COUNT"],
            is_aggregate_query=True,
            is_valid=True,
        )
        
        decision = self.engine.evaluate(analysis)
        
        assert decision.action == "DP"
        assert "epsilon" in decision.params
    
    def test_deid_decision_for_sensitive_columns(self):
        """测试敏感列查询应返回DeID决策"""
        analysis = AnalysisResult(
            tables=["users"],
            select_columns=["name", "email"],
            is_aggregate_query=False,
            is_valid=True,
        )
        
        decision = self.engine.evaluate(analysis)
        
        assert decision.action == "DeID"
        assert "columns" in decision.params
    
    def test_pass_decision_for_non_sensitive(self):
        """测试非敏感查询应返回PASS决策"""
        analysis = AnalysisResult(
            tables=["users"],
            select_columns=["id", "status"],
            is_aggregate_query=False,
            is_valid=True,
        )
        
        decision = self.engine.evaluate(analysis)
        
        assert decision.action == "PASS"
    
    def test_reject_invalid_sql(self):
        """测试无效SQL应返回REJECT决策"""
        analysis = AnalysisResult(
            is_valid=False,
            error_message="Syntax error",
        )
        
        decision = self.engine.evaluate(analysis)
        
        assert decision.action == "REJECT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

