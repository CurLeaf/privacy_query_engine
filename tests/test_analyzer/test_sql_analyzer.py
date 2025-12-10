"""
SQL Analyzer 单元测试
"""
import pytest
from main.analyzer import SQLAnalyzer, AnalysisResult


class TestSQLAnalyzer:
    """SQLAnalyzer测试类"""
    
    def setup_method(self):
        self.analyzer = SQLAnalyzer()
    
    def test_analyze_count_query(self):
        """测试COUNT查询分析"""
        sql = "SELECT COUNT(*) FROM users"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert result.is_aggregate_query
        assert "COUNT" in result.aggregations
        assert "users" in result.tables
    
    def test_analyze_select_query(self):
        """测试普通SELECT查询分析"""
        sql = "SELECT name, email FROM users WHERE age > 30"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert not result.is_aggregate_query
        assert result.has_where
        assert "users" in result.tables
    
    def test_analyze_with_aggregations(self):
        """测试多聚合函数查询"""
        sql = "SELECT COUNT(*), SUM(amount), AVG(price) FROM orders"
        result = self.analyzer.analyze(sql)
        
        assert result.is_aggregate_query
        assert "COUNT" in result.aggregations
        assert "SUM" in result.aggregations
        assert "AVG" in result.aggregations
    
    def test_has_aggregation_method(self):
        """测试has_aggregation方法"""
        sql = "SELECT COUNT(*) FROM users"
        result = self.analyzer.analyze(sql)
        
        assert result.has_aggregation("COUNT")
        assert result.has_aggregation("count")  # 大小写不敏感
        assert not result.has_aggregation("SUM")
    
    def test_has_sensitive_columns(self):
        """测试敏感列检测"""
        sql = "SELECT name, email FROM users"
        result = self.analyzer.analyze(sql)
        
        sensitive_list = ["name", "email", "phone"]
        assert result.has_sensitive_columns(sensitive_list)
    
    def test_extract_group_by(self):
        """测试GROUP BY提取"""
        sql = "SELECT department, COUNT(*) FROM employees GROUP BY department"
        result = self.analyzer.analyze(sql)
        
        assert "department" in result.group_by_columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

