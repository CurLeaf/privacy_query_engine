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
    
    def test_analyze_inner_join(self):
        """测试INNER JOIN分析"""
        sql = "SELECT u.name, o.amount FROM users u INNER JOIN orders o ON u.id = o.user_id"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.joins) == 1
        assert result.joins[0].join_type == "INNER"
        assert "users" in result.joins[0].tables
        assert "orders" in result.joins[0].tables
        assert len(result.joins[0].join_conditions) == 1
        assert "u.id = o.user_id" in result.joins[0].join_conditions
    
    def test_analyze_left_join(self):
        """测试LEFT JOIN分析"""
        sql = "SELECT u.name, o.amount FROM users u LEFT JOIN orders o ON u.id = o.user_id"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.joins) == 1
        assert result.joins[0].join_type == "LEFT"
        assert "users" in result.joins[0].tables
        assert "orders" in result.joins[0].tables
    
    def test_analyze_multiple_joins(self):
        """测试多个JOIN分析"""
        sql = """SELECT u.name, o.amount, p.name 
                 FROM users u 
                 INNER JOIN orders o ON u.id = o.user_id 
                 LEFT JOIN products p ON o.product_id = p.id"""
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.joins) == 2
        assert result.joins[0].join_type == "INNER"
        assert result.joins[1].join_type == "LEFT"
        assert "users" in result.tables
        assert "orders" in result.tables
        assert "products" in result.tables
    
    def test_analyze_join_with_and_conditions(self):
        """测试包含AND条件的JOIN"""
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id AND u.status = 'active'"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.joins) == 1
        assert len(result.joins[0].join_conditions) == 2
        assert "u.id = o.user_id" in result.joins[0].join_conditions
        assert "u.status = 'active'" in result.joins[0].join_conditions
    
    def test_analyze_joins_method(self):
        """测试analyze_joins公共方法"""
        sql = "SELECT * FROM users u RIGHT JOIN orders o ON u.id = o.user_id"
        joins = self.analyzer.analyze_joins(sql)
        
        assert len(joins) == 1
        assert joins[0].join_type == "RIGHT"
        assert "users" in joins[0].tables
        assert "orders" in joins[0].tables
    
    def test_analyze_subquery_in_where(self):
        """测试WHERE子句中的子查询分析"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.subqueries) == 1
        assert result.subqueries[0].subquery_type == "IN"
        assert result.subqueries[0].location == "WHERE"
        assert "orders" in result.subqueries[0].tables
    
    def test_analyze_exists_subquery(self):
        """测试EXISTS子查询分析"""
        sql = "SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id)"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.subqueries) == 1
        assert result.subqueries[0].subquery_type == "EXISTS"
        assert result.subqueries[0].is_correlated == True
    
    def test_analyze_scalar_subquery(self):
        """测试标量子查询分析"""
        sql = "SELECT name, (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count FROM users"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.subqueries) == 1
        assert result.subqueries[0].subquery_type == "SCALAR"
    
    def test_analyze_simple_cte(self):
        """测试简单CTE分析"""
        sql = """
        WITH active_users AS (
            SELECT * FROM users WHERE status = 'active'
        )
        SELECT * FROM active_users
        """
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.ctes) == 1
        assert result.ctes[0].name == "active_users"
        assert result.ctes[0].is_recursive == False
    
    def test_analyze_recursive_cte(self):
        """测试递归CTE分析"""
        sql = """
        WITH RECURSIVE employee_hierarchy AS (
            SELECT id, name, manager_id FROM employees WHERE manager_id IS NULL
            UNION ALL
            SELECT e.id, e.name, e.manager_id FROM employees e
            JOIN employee_hierarchy eh ON e.manager_id = eh.id
        )
        SELECT * FROM employee_hierarchy
        """
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.ctes) == 1
        assert result.ctes[0].name == "employee_hierarchy"
        assert result.ctes[0].is_recursive == True
    
    def test_extract_subqueries_method(self):
        """测试extract_subqueries公共方法"""
        sql = "SELECT * FROM users WHERE age > (SELECT AVG(age) FROM users)"
        subqueries = self.analyzer.extract_subqueries(sql)
        
        assert len(subqueries) == 1
        assert "AVG" in subqueries[0].sql.upper()
    
    def test_extract_ctes_method(self):
        """测试extract_ctes公共方法"""
        sql = "WITH temp AS (SELECT * FROM users) SELECT * FROM temp"
        ctes = self.analyzer.extract_ctes(sql)
        
        assert len(ctes) == 1
        assert ctes[0].name == "temp"
    
    def test_analyze_row_number_window_function(self):
        """测试ROW_NUMBER窗口函数分析"""
        sql = "SELECT name, ROW_NUMBER() OVER (ORDER BY created_at) as row_num FROM users"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.window_functions) == 1
        assert result.window_functions[0].function_name == "ROW_NUMBER"
        assert "created_at" in result.window_functions[0].order_by[0]
    
    def test_analyze_window_function_with_partition(self):
        """测试带PARTITION BY的窗口函数"""
        sql = "SELECT department, name, SUM(salary) OVER (PARTITION BY department ORDER BY hire_date) as running_total FROM employees"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.window_functions) == 1
        assert result.window_functions[0].function_name == "SUM"
        assert "department" in result.window_functions[0].partition_by
        assert "hire_date" in result.window_functions[0].order_by[0]
    
    def test_analyze_multiple_window_functions(self):
        """测试多个窗口函数"""
        sql = """SELECT name, 
                 ROW_NUMBER() OVER (ORDER BY id) as row_num,
                 RANK() OVER (PARTITION BY department ORDER BY salary DESC) as salary_rank
                 FROM employees"""
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.window_functions) == 2
        func_names = [wf.function_name for wf in result.window_functions]
        assert "ROW_NUMBER" in func_names
        assert "RANK" in func_names
    
    def test_analyze_window_function_with_frame(self):
        """测试带窗口框架的窗口函数"""
        sql = "SELECT date, amount, SUM(amount) OVER (ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_sum FROM sales"
        result = self.analyzer.analyze(sql)
        
        assert result.is_valid
        assert len(result.window_functions) == 1
        assert result.window_functions[0].window_frame is not None
        assert "ROWS" in result.window_functions[0].window_frame.upper()
    
    def test_analyze_window_functions_method(self):
        """测试analyze_window_functions公共方法"""
        sql = "SELECT name, LAG(salary, 1) OVER (ORDER BY hire_date) as prev_salary FROM employees"
        window_funcs = self.analyzer.analyze_window_functions(sql)
        
        assert len(window_funcs) == 1
        assert window_funcs[0].function_name == "LAG"
        assert "salary" in window_funcs[0].arguments


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
