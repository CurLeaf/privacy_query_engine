"""
QueryExecutor 查询执行器测试
"""
import os
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from main.executor import QueryExecutor, QueryResult, ExecutionMode
from main.executor.database import DatabaseConnection
from main.models import User, Order

ENV_DB_CFG = {
    "host": "localhost",
    "port": 5432,
    "database": "privacy",
    "user": "postgres",
    "password": "123456",
}


class TestQueryResult:
    """QueryResult 数据类测试"""
    
    def test_default_values(self):
        """测试默认值"""
        result = QueryResult()
        assert result.success is True
        assert result.data is None
        assert result.row_count == 0
        assert result.privacy_applied is False
        assert result.privacy_info == {}
        assert result.error is None
        assert result.original_query == ""
        assert result.execution_mode == "sql"
    
    def test_custom_values(self):
        """测试自定义值"""
        result = QueryResult(
            success=True,
            data=[{"id": 1, "name": "test"}],
            row_count=1,
            privacy_applied=True,
            privacy_info={"type": "DP", "epsilon": 1.0},
            original_query="SELECT * FROM users",
            execution_mode="orm"
        )
        assert result.success is True
        assert result.row_count == 1
        assert result.privacy_applied is True
        assert result.privacy_info["type"] == "DP"
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = QueryResult(
            success=True,
            data={"count": 10},
            row_count=1
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["success"] is True
        assert d["data"] == {"count": 10}
        assert d["row_count"] == 1
    
    def test_error_result(self):
        """测试错误结果"""
        result = QueryResult(
            success=False,
            error="Connection failed",
            original_query="SELECT 1"
        )
        assert result.success is False
        assert result.error == "Connection failed"


class TestExecutionMode:
    """ExecutionMode 枚举测试"""
    
    def test_enum_values(self):
        """测试枚举值"""
        assert ExecutionMode.ORM.value == "orm"
        assert ExecutionMode.SQL.value == "sql"
        assert ExecutionMode.MOCK.value == "mock"
    
    def test_string_comparison(self):
        """测试字符串比较"""
        assert ExecutionMode.ORM == "orm"
        assert ExecutionMode.SQL == "sql"
        assert ExecutionMode.MOCK == "mock"


class TestQueryExecutorInit:
    """QueryExecutor 初始化测试"""
    
    def test_create_mock_executor(self):
        """测试创建 Mock 执行器"""
        executor = QueryExecutor.create(mode=ExecutionMode.MOCK)
        assert executor.mode == ExecutionMode.MOCK
        assert executor.mock_executor is not None
        assert executor.db is None
    
    def test_create_with_params(self):
        """测试带参数创建"""
        executor = QueryExecutor.create(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="secret",
            mode=ExecutionMode.SQL
        )
        assert executor.mode == ExecutionMode.SQL
        assert executor.db is not None
        assert executor.db.config.host == "localhost"
        assert executor.db.config.database == "testdb"
    
    def test_from_env(self):
        """测试从环境变量创建"""
        with patch.dict(os.environ, {
            "PG_HOST": "env_host",
            "PG_PORT": "5432",
            "PG_DATABASE": "env_db",
            "PG_USER": "env_user",
            "PG_PASSWORD": "env_pass",
        }):
            executor = QueryExecutor.from_env(mode=ExecutionMode.SQL)
            assert executor.db.config.host == "env_host"
            assert executor.db.config.database == "env_db"
    
    def test_from_env_mock_mode(self):
        """测试 Mock 模式从环境变量创建"""
        executor = QueryExecutor.from_env(mode=ExecutionMode.MOCK)
        assert executor.mode == ExecutionMode.MOCK
        assert executor.db is None
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with patch.object(QueryExecutor, 'close') as mock_close:
            with QueryExecutor.create(mode=ExecutionMode.MOCK) as executor:
                assert executor is not None
            mock_close.assert_called_once()


class TestQueryExecutorMockMode:
    """QueryExecutor Mock 模式测试"""
    
    @pytest.fixture
    def executor(self):
        """创建 Mock 执行器 fixture"""
        return QueryExecutor.create(mode=ExecutionMode.MOCK)
    
    def test_execute_sql_select(self, executor):
        """测试 Mock 模式执行 SELECT"""
        result = executor.execute_sql("SELECT * FROM users")
        assert result.success is True
        assert result.execution_mode == "mock"
        assert isinstance(result.data, list)
    
    def test_execute_sql_count(self, executor):
        """测试 Mock 模式执行 COUNT"""
        result = executor.execute_sql("SELECT COUNT(*) FROM users")
        assert result.success is True
        assert isinstance(result.data, int)
    
    def test_execute_scalar(self, executor):
        """测试 Mock 模式执行标量查询"""
        result = executor.execute_scalar("SELECT COUNT(*) FROM users")
        assert isinstance(result, int)
    
    def test_execute_query(self, executor):
        """测试 Mock 模式执行查询"""
        result = executor.execute_query("SELECT * FROM users")
        assert isinstance(result, list)
    
    def test_test_connection_mock(self, executor):
        """测试 Mock 模式连接测试"""
        result = executor.test_connection()
        assert result["status"] == "mock"


class TestQueryExecutorNoConnection:
    """QueryExecutor 无连接错误测试"""
    
    def test_ensure_db_connection_error(self):
        """测试无数据库连接时的错误"""
        executor = QueryExecutor(db_connection=None, mode=ExecutionMode.SQL)
        
        with pytest.raises(RuntimeError) as exc_info:
            executor.get_all(User)
        
        assert "No database connection available" in str(exc_info.value)


class TestQueryExecutorIntegration:
    """
    QueryExecutor 集成测试
    需要实际的 PostgreSQL 数据库

    运行方式:
        pytest tests/test_executor/test_query_executor.py::TestQueryExecutorIntegration -v -m integration
    """
    
    @pytest.fixture
    def executor(self):
        """创建执行器 fixture"""
        executor = QueryExecutor.create(
            host=ENV_DB_CFG["host"],
            port=ENV_DB_CFG["port"],
            database=ENV_DB_CFG["database"],
            user=ENV_DB_CFG["user"],
            password=ENV_DB_CFG["password"],
            mode=ExecutionMode.SQL
        )
        yield executor
        executor.close()
    
    @pytest.mark.integration
    def test_test_connection(self, executor):
        """测试数据库连接"""
        result = executor.test_connection()
        assert result["status"] == "connected"
        assert "version" in result
    
    @pytest.mark.integration
    def test_execute_sql_select(self, executor):
        """测试执行 SELECT 查询"""
        result = executor.execute_sql("SELECT 1 as num, 'test' as text;")
        assert result.success is True
        assert result.row_count == 1
        assert result.data[0]["num"] == 1
        assert result.data[0]["text"] == "test"
    
    @pytest.mark.integration
    def test_execute_sql_count(self, executor):
        """测试执行聚合查询"""
        result = executor.execute_sql("SELECT COUNT(*) FROM users;")
        assert result.success is True
        assert isinstance(result.data, int)
    
    @pytest.mark.integration
    def test_execute_scalar(self, executor):
        """测试执行标量查询"""
        result = executor.execute_scalar("SELECT COUNT(*) FROM users;")
        assert isinstance(result, int)
        assert result >= 0
    
    @pytest.mark.integration
    def test_execute_query(self, executor):
        """测试执行查询返回列表"""
        result = executor.execute_query("SELECT * FROM users LIMIT 5;")
        assert isinstance(result, list)
    
    @pytest.mark.integration
    def test_get_tables(self, executor):
        """测试获取表列表"""
        tables = executor.get_tables()
        assert isinstance(tables, list)
        assert "users" in tables
        assert "orders" in tables
    
    @pytest.mark.integration
    def test_get_table_columns(self, executor):
        """测试获取表列信息"""
        columns = executor.get_table_columns("users")
        assert isinstance(columns, list)
        column_names = [col["column_name"] for col in columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "email" in column_names


class TestQueryExecutorORMIntegration:
    """
    QueryExecutor ORM 操作集成测试
    需要实际的 PostgreSQL 数据库

    运行方式:
        pytest tests/test_executor/test_query_executor.py::TestQueryExecutorORMIntegration -v -m integration
    """
    
    @pytest.fixture
    def executor(self):
        """创建执行器 fixture"""
        executor = QueryExecutor.create(
            host=ENV_DB_CFG["host"],
            port=ENV_DB_CFG["port"],
            database=ENV_DB_CFG["database"],
            user=ENV_DB_CFG["user"],
            password=ENV_DB_CFG["password"],
            mode=ExecutionMode.ORM
        )
        yield executor
        executor.close()
    
    @pytest.mark.integration
    def test_get_all_users(self, executor):
        """测试获取所有用户"""
        users = executor.get_all(User)
        assert isinstance(users, (list, tuple))
        if users:
            assert isinstance(users[0], User)
    
    @pytest.mark.integration
    def test_get_by_id(self, executor):
        """测试根据 ID 获取"""
        users = executor.get_all(User)
        if users:
            user = executor.get_by_id(User, users[0].id)
            assert user is not None
            assert user.id == users[0].id
    
    @pytest.mark.integration
    def test_get_by_field(self, executor):
        """测试根据字段查询"""
        users = executor.get_all(User)
        if users:
            result = executor.get_by_field(User, "email", users[0].email)
            assert len(result) > 0
            assert result[0].email == users[0].email
    
    @pytest.mark.integration
    def test_get_one(self, executor):
        """测试获取单个记录"""
        users = executor.get_all(User)
        if users:
            user = executor.get_one(User, "email", users[0].email)
            assert user is not None
            assert user.email == users[0].email
    
    @pytest.mark.integration
    def test_count(self, executor):
        """测试统计数量"""
        count = executor.count(User)
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.integration
    def test_custom_query(self, executor):
        """测试自定义查询"""
        from sqlmodel import select
        
        statement = select(User).where(User.age >= 25)
        users = executor.query(statement)
        
        for user in users:
            assert user.age >= 25
    
    @pytest.mark.integration
    def test_query_one(self, executor):
        """测试自定义查询返回单个结果"""
        from sqlmodel import select
        
        statement = select(User).limit(1)
        user = executor.query_one(statement)
        
        if user:
            assert isinstance(user, User)
    
    @pytest.mark.integration
    def test_get_all_orders(self, executor):
        """测试获取所有订单"""
        orders = executor.get_all(Order)
        assert isinstance(orders, (list, tuple))
        if orders:
            assert isinstance(orders[0], Order)
            assert isinstance(orders[0].amount, Decimal)


class TestQueryExecutorPrivacy:
    """
    QueryExecutor 隐私保护测试
    """
    
    @pytest.fixture
    def executor(self):
        """创建 Mock 执行器 fixture"""
        return QueryExecutor.create(mode=ExecutionMode.MOCK)
    
    def test_execute_with_privacy_pass(self, executor):
        """测试 PASS 策略（无隐私保护）"""
        from main.analyzer import AnalysisResult
        from main.policy import PolicyDecision
        
        analysis = AnalysisResult(
            tables=["users"],
            select_columns=["id", "name"],
            original_sql="SELECT id, name FROM users"
        )
        
        policy = PolicyDecision(action="PASS")
        
        result = executor.execute_with_privacy(
            sql="SELECT id, name FROM users",
            analysis_result=analysis,
            policy_decision=policy
        )
        
        assert result.success is True
        assert result.privacy_applied is False
    
    def test_execute_with_privacy_reject(self, executor):
        """测试 REJECT 策略"""
        from main.analyzer import AnalysisResult
        from main.policy import PolicyDecision
        
        analysis = AnalysisResult(
            tables=["users"],
            select_columns=["*"],
            original_sql="SELECT * FROM users"
        )
        
        policy = PolicyDecision(
            action="REJECT",
            reason="查询包含敏感数据"
        )
        
        result = executor.execute_with_privacy(
            sql="SELECT * FROM users",
            analysis_result=analysis,
            policy_decision=policy
        )
        
        assert result.success is False
        assert result.error == "查询包含敏感数据"
    
    def test_execute_legacy_interface(self, executor):
        """测试兼容旧接口"""
        from main.analyzer import AnalysisResult
        from main.policy import PolicyDecision
        
        analysis = AnalysisResult(
            tables=["users"],
            select_columns=["id"],
            original_sql="SELECT id FROM users"
        )
        
        policy = PolicyDecision(action="PASS")
        
        result = executor.execute(
            original_sql="SELECT id FROM users",
            analysis_result=analysis,
            policy_decision=policy
        )
        
        assert isinstance(result, dict)
        assert "type" in result
        assert "original_query" in result
        assert "protected_result" in result


class TestQueryExecutorHelpers:
    """QueryExecutor 辅助方法测试"""
    
    def test_is_aggregate_query(self):
        """测试聚合查询判断"""
        executor = QueryExecutor.create(mode=ExecutionMode.MOCK)
        
        assert executor._is_aggregate_query("SELECT COUNT(*) FROM users") is True
        assert executor._is_aggregate_query("SELECT SUM(amount) FROM orders") is True
        assert executor._is_aggregate_query("SELECT AVG(age) FROM users") is True
        assert executor._is_aggregate_query("SELECT MIN(id) FROM users") is True
        assert executor._is_aggregate_query("SELECT MAX(age) FROM users") is True
        assert executor._is_aggregate_query("SELECT * FROM users") is False
        assert executor._is_aggregate_query("SELECT id, name FROM users") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

