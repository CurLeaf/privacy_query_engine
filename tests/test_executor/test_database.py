"""
数据库连接单元测试
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from main.executor.database import DatabaseConnection, DatabaseConfig

ENV_DB_CFG = {
    "host": "localhost",
    "port": 5432,
    "database": "privacy",
    "user": "postgres",
    "password": "123456",
}

class TestDatabaseConfig:
    """DatabaseConfig 测试类"""
    
    def test_default_values(self):
        """测试默认值"""
        # 用例中用 .env 文件的默认配置做mock
        with patch.dict(os.environ, {
            "PG_HOST": "localhost",
            "PG_PORT": "5432",
            "PG_DATABASE": "privacy",
            "PG_USER": "postgres",
            "PG_PASSWORD": "123456",
        }):
            config = DatabaseConfig()
            assert config.host == "localhost"
            assert config.port == 5432
            assert config.database == "privacy"
            assert config.user == "postgres"
            assert config.password == "123456"
    
    def test_custom_values(self):
        """测试自定义值"""
        config = DatabaseConfig(
            host="myhost",
            port=5433,
            database="mydb",
            user="myuser",
            password="mypass",
        )
        assert config.host == "myhost"
        assert config.port == 5433
        assert config.database == "mydb"
        assert config.user == "myuser"
        assert config.password == "mypass"
    
    def test_connection_string(self):
        """测试连接字符串生成"""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="secret",
        )
        conn_str = config.to_connection_string()
        assert "postgresql+psycopg2://" in conn_str
        assert "admin:secret@localhost:5432/testdb" in conn_str
    
    def test_password_url_encoding(self):
        """测试密码中特殊字符的URL编码"""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="p@ss#word!",
        )
        conn_str = config.to_connection_string()
        # 特殊字符应该被编码
        assert "p%40ss%23word%21" in conn_str
    
    @patch.dict(os.environ, {
        "PG_HOST": "env_host",
        "PG_PORT": "5433",
        "PG_DATABASE": "env_db",
        "PG_USER": "env_user",
        "PG_PASSWORD": "env_pass",
    })
    def test_env_variables(self):
        """测试从环境变量读取配置"""
        config = DatabaseConfig()
        assert config.host == "env_host"
        assert config.port == 5433
        assert config.database == "env_db"
        assert config.user == "env_user"
        assert config.password == "env_pass"


class TestDatabaseConnection:
    """DatabaseConnection 测试类"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        with patch.dict(os.environ, {
            "PG_HOST": ENV_DB_CFG["host"],
            "PG_PORT": str(ENV_DB_CFG["port"]),
            "PG_DATABASE": ENV_DB_CFG["database"],
            "PG_USER": ENV_DB_CFG["user"],
            "PG_PASSWORD": ENV_DB_CFG["password"],
        }):
            db = DatabaseConnection()
            assert db.config is not None
            assert db.pool_size == 5
            assert db.max_overflow == 10
            assert db.echo is False
    
    def test_init_with_params(self):
        """测试带参数初始化"""
        db = DatabaseConnection(
            host="myhost",
            port=5433,
            database="mydb",
            user="admin",
            password="secret",
            pool_size=10,
            echo=True,
        )
        assert db.config.host == "myhost"
        assert db.config.port == 5433
        assert db.pool_size == 10
        assert db.echo is True
    
    def test_connection_string_property(self):
        """测试连接字符串属性"""
        db = DatabaseConnection(
            host="localhost",
            database="testdb",
            user="postgres",
            password="pass",
        )
        conn_str = db.connection_string
        assert "postgresql+psycopg2://" in conn_str
        assert "localhost" in conn_str
        assert "testdb" in conn_str
    
    def test_from_env(self):
        """测试从环境变量创建"""
        with patch.dict(os.environ, {
            "PG_HOST": ENV_DB_CFG["host"]
        }):
            db = DatabaseConnection.from_env()
            assert db.config.host == ENV_DB_CFG["host"]
    
    def test_context_manager(self):
        """测试上下文管理器支持"""
        # 使用mock避免实际连接
        with patch.object(DatabaseConnection, 'close') as mock_close:
            with DatabaseConnection() as db:
                assert db is not None
            mock_close.assert_called_once()


class TestDatabaseConnectionIntegration:
    """
    数据库连接集成测试
    需要实际的PostgreSQL数据库

    运行方式:
        pytest tests/test_executor/test_database.py -v -m integration
    """

    @pytest.mark.integration
    @pytest.mark.skipif(
        not (
            ENV_DB_CFG["host"]
            and ENV_DB_CFG["port"]
            and ENV_DB_CFG["database"]
            and ENV_DB_CFG["user"]
        ),
        reason="需要设置 .env 的数据库环境变量才能运行集成测试"
    )
    def test_real_connection(self):
        """测试真实数据库连接"""
        db = DatabaseConnection(
            host=ENV_DB_CFG["host"],
            port=ENV_DB_CFG["port"],
            database=ENV_DB_CFG["database"],
            user=ENV_DB_CFG["user"],
            password=ENV_DB_CFG["password"],
        )
        result = db.test_connection()
        assert result["status"] == "connected"
        assert "version" in result
        db.close()

    @pytest.mark.integration
    @pytest.mark.skipif(
        not (
            ENV_DB_CFG["host"]
            and ENV_DB_CFG["port"]
            and ENV_DB_CFG["database"]
            and ENV_DB_CFG["user"]
        ),
        reason="需要设置 .env 的数据库环境变量才能运行集成测试"
    )
    def test_execute_query(self):
        """测试执行查询"""
        db = DatabaseConnection(
            host=ENV_DB_CFG["host"],
            port=ENV_DB_CFG["port"],
            database=ENV_DB_CFG["database"],
            user=ENV_DB_CFG["user"],
            password=ENV_DB_CFG["password"],
        )
        result = db.execute_query("SELECT 1 as num, 'test' as text;")
        assert len(result) == 1
        assert result[0]["num"] == 1
        assert result[0]["text"] == "test"
        db.close()

    @pytest.mark.integration
    @pytest.mark.skipif(
        not (
            ENV_DB_CFG["host"]
            and ENV_DB_CFG["port"]
            and ENV_DB_CFG["database"]
            and ENV_DB_CFG["user"]
        ),
        reason="需要设置 .env 的数据库环境变量才能运行集成测试"
    )
    def test_execute_scalar(self):
        """测试执行标量查询"""
        db = DatabaseConnection(
            host=ENV_DB_CFG["host"],
            port=ENV_DB_CFG["port"],
            database=ENV_DB_CFG["database"],
            user=ENV_DB_CFG["user"],
            password=ENV_DB_CFG["password"],
        )
        result = db.execute_scalar("SELECT COUNT(*) FROM information_schema.tables;")
        assert isinstance(result, int)
        assert result > 0
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

