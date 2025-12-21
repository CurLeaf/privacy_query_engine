"""
MultiDatabaseConnector - 多数据库连接器
支持 PostgreSQL 和 MySQL 数据库
"""
import os
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from contextlib import contextmanager
from urllib.parse import quote_plus
from enum import Enum
from dataclasses import dataclass, field

from sqlmodel import SQLModel, create_engine, Session, select, text
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
from sqlalchemy.exc import OperationalError, DatabaseError


class DatabaseType(Enum):
    """数据库类型"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_type: DatabaseType = DatabaseType.POSTGRESQL
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: str = ""
    charset: str = "utf8mb4"  # MySQL专用
    ssl_mode: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_connection_string(self) -> str:
        """生成连接字符串"""
        encoded_password = quote_plus(self.password) if self.password else ""
        
        if self.db_type == DatabaseType.POSTGRESQL:
            base_url = f"postgresql+psycopg2://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"
            params = []
            if self.ssl_mode:
                params.append(f"sslmode={self.ssl_mode}")
            if params:
                base_url += "?" + "&".join(params)
            return base_url
        
        elif self.db_type == DatabaseType.MYSQL:
            base_url = f"mysql+pymysql://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"
            params = [f"charset={self.charset}"]
            if self.ssl_mode:
                params.append(f"ssl_mode={self.ssl_mode}")
            return base_url + "?" + "&".join(params)
        
        elif self.db_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"
        
        raise ValueError(f"Unsupported database type: {self.db_type}")
    
    @classmethod
    def from_env(cls, prefix: str = "") -> "DatabaseConfig":
        """从环境变量创建配置"""
        db_type_str = os.getenv(f"{prefix}DB_TYPE", "postgresql").lower()
        db_type = DatabaseType(db_type_str)
        
        default_port = 5432 if db_type == DatabaseType.POSTGRESQL else 3306
        
        return cls(
            db_type=db_type,
            host=os.getenv(f"{prefix}DB_HOST", "localhost"),
            port=int(os.getenv(f"{prefix}DB_PORT", str(default_port))),
            database=os.getenv(f"{prefix}DB_DATABASE", "postgres"),
            user=os.getenv(f"{prefix}DB_USER", "postgres"),
            password=os.getenv(f"{prefix}DB_PASSWORD", ""),
            charset=os.getenv(f"{prefix}DB_CHARSET", "utf8mb4"),
            ssl_mode=os.getenv(f"{prefix}DB_SSL_MODE"),
        )


@dataclass
class ConnectionPoolConfig:
    """连接池配置"""
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 连接回收时间（秒）
    pool_pre_ping: bool = True  # 自动检测断开的连接


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒
    exponential_backoff: bool = True


class ConnectionError(Exception):
    """连接错误"""
    pass


class SchemaChange:
    """模式变更信息"""
    def __init__(
        self,
        change_type: str,
        table_name: str,
        column_name: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None
    ):
        self.change_type = change_type  # "added", "removed", "modified"
        self.table_name = table_name
        self.column_name = column_name
        self.old_value = old_value
        self.new_value = new_value
    
    def __repr__(self):
        return f"SchemaChange({self.change_type}, {self.table_name}, {self.column_name})"


class MultiDatabaseConnector:
    """多数据库连接器"""
    
    def __init__(
        self,
        config: DatabaseConfig,
        pool_config: Optional[ConnectionPoolConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        echo: bool = False
    ):
        """
        初始化多数据库连接器
        
        Args:
            config: 数据库配置
            pool_config: 连接池配置
            retry_config: 重试配置
            echo: 是否打印SQL语句
        """
        self.config = config
        self.pool_config = pool_config or ConnectionPoolConfig()
        self.retry_config = retry_config or RetryConfig()
        self.echo = echo
        self._engine = None
        self._schema_cache: Dict[str, List[Dict]] = {}
    
    @property
    def db_type(self) -> DatabaseType:
        """获取数据库类型"""
        return self.config.db_type
    
    @property
    def connection_string(self) -> str:
        """获取连接字符串"""
        return self.config.to_connection_string()
    
    @property
    def engine(self):
        """懒加载数据库引擎"""
        if self._engine is None:
            self._engine = self._create_engine_with_retry()
        return self._engine
    
    def _create_engine_with_retry(self):
        """创建数据库引擎（带重试）"""
        last_error = None
        
        for attempt in range(self.retry_config.max_retries):
            try:
                engine = create_engine(
                    self.connection_string,
                    echo=self.echo,
                    poolclass=QueuePool,
                    pool_size=self.pool_config.pool_size,
                    max_overflow=self.pool_config.max_overflow,
                    pool_timeout=self.pool_config.pool_timeout,
                    pool_recycle=self.pool_config.pool_recycle,
                    pool_pre_ping=self.pool_config.pool_pre_ping,
                )
                
                # 测试连接
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                return engine
                
            except (OperationalError, DatabaseError) as e:
                last_error = e
                if attempt < self.retry_config.max_retries - 1:
                    delay = self.retry_config.retry_delay
                    if self.retry_config.exponential_backoff:
                        delay *= (2 ** attempt)
                    time.sleep(delay)
        
        raise ConnectionError(
            f"Failed to connect to database after {self.retry_config.max_retries} attempts: {last_error}"
        )
    
    @contextmanager
    def get_session(self, expire_on_commit: bool = False):
        """获取数据库会话"""
        session = Session(self.engine, expire_on_commit=expire_on_commit)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            with self.get_session() as session:
                if self.db_type == DatabaseType.POSTGRESQL:
                    result = session.execute(text("SELECT version();"))
                    version = result.scalar()
                    result = session.execute(text("SELECT current_database();"))
                    current_db = result.scalar()
                elif self.db_type == DatabaseType.MYSQL:
                    result = session.execute(text("SELECT VERSION();"))
                    version = result.scalar()
                    result = session.execute(text("SELECT DATABASE();"))
                    current_db = result.scalar()
                else:
                    version = "unknown"
                    current_db = self.config.database
                
                return {
                    "status": "connected",
                    "db_type": self.db_type.value,
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": current_db,
                    "version": version,
                }
        except Exception as e:
            return {
                "status": "failed",
                "db_type": self.db_type.value,
                "error": str(e),
                "host": self.config.host,
                "port": self.config.port,
            }
    
    def execute_query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行查询"""
        # 处理方言差异
        sql = self._adapt_sql_dialect(sql)
        
        with self.get_session() as session:
            if params:
                result = session.execute(text(sql), params)
            else:
                result = session.execute(text(sql))
            
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def execute_scalar(self, sql: str, params: Dict[str, Any] = None) -> Any:
        """执行查询并返回单个值"""
        sql = self._adapt_sql_dialect(sql)
        
        with self.get_session() as session:
            if params:
                result = session.execute(text(sql), params)
            else:
                result = session.execute(text(sql))
            return result.scalar()
    
    def _adapt_sql_dialect(self, sql: str) -> str:
        """适配SQL方言差异"""
        if self.db_type == DatabaseType.MYSQL:
            # PostgreSQL -> MySQL 转换
            sql = sql.replace("ILIKE", "LIKE")
            sql = sql.replace("::text", "")
            sql = sql.replace("::integer", "")
            sql = sql.replace("SERIAL", "AUTO_INCREMENT")
            # 处理布尔值
            sql = sql.replace("TRUE", "1").replace("FALSE", "0")
        
        elif self.db_type == DatabaseType.POSTGRESQL:
            # MySQL -> PostgreSQL 转换
            sql = sql.replace("AUTO_INCREMENT", "SERIAL")
            sql = sql.replace("LIMIT 1", "LIMIT 1")  # 保持不变
        
        return sql
    
    def get_tables(self) -> List[str]:
        """获取所有表名"""
        if self.db_type == DatabaseType.POSTGRESQL:
            sql = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
        elif self.db_type == DatabaseType.MYSQL:
            sql = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY table_name;
            """
        else:
            return []
        
        result = self.execute_query(sql)
        return [row["table_name"] for row in result]
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        if self.db_type == DatabaseType.POSTGRESQL:
            sql = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table_name
                ORDER BY ordinal_position;
            """
        elif self.db_type == DatabaseType.MYSQL:
            sql = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = :table_name
                ORDER BY ordinal_position;
            """
        else:
            return []
        
        return self.execute_query(sql, {"table_name": table_name})
    
    def detect_schema_changes(self) -> List[SchemaChange]:
        """检测模式变更"""
        changes = []
        current_schema = {}
        
        # 获取当前模式
        for table in self.get_tables():
            current_schema[table] = self.get_table_columns(table)
        
        # 比较与缓存的模式
        if self._schema_cache:
            # 检查新增的表
            for table in current_schema:
                if table not in self._schema_cache:
                    changes.append(SchemaChange("added", table))
                else:
                    # 检查列变更
                    old_columns = {c["column_name"]: c for c in self._schema_cache[table]}
                    new_columns = {c["column_name"]: c for c in current_schema[table]}
                    
                    for col_name in new_columns:
                        if col_name not in old_columns:
                            changes.append(SchemaChange("added", table, col_name))
                        elif new_columns[col_name] != old_columns[col_name]:
                            changes.append(SchemaChange(
                                "modified", table, col_name,
                                old_columns[col_name], new_columns[col_name]
                            ))
                    
                    for col_name in old_columns:
                        if col_name not in new_columns:
                            changes.append(SchemaChange("removed", table, col_name))
            
            # 检查删除的表
            for table in self._schema_cache:
                if table not in current_schema:
                    changes.append(SchemaChange("removed", table))
        
        # 更新缓存
        self._schema_cache = current_schema
        
        return changes
    
    def refresh_schema_cache(self):
        """刷新模式缓存"""
        self._schema_cache = {}
        for table in self.get_tables():
            self._schema_cache[table] = self.get_table_columns(table)
    
    def get_connection_pool_status(self) -> Dict[str, Any]:
        """获取连接池状态"""
        if self._engine is None:
            return {"status": "not_initialized"}
        
        pool = self._engine.pool
        return {
            "status": "active",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    
    def close(self):
        """关闭连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    @classmethod
    def create_postgresql(
        cls,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
        password: str = "",
        **kwargs
    ) -> "MultiDatabaseConnector":
        """创建PostgreSQL连接器"""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        return cls(config, **kwargs)
    
    @classmethod
    def create_mysql(
        cls,
        host: str = "localhost",
        port: int = 3306,
        database: str = "mysql",
        user: str = "root",
        password: str = "",
        charset: str = "utf8mb4",
        **kwargs
    ) -> "MultiDatabaseConnector":
        """创建MySQL连接器"""
        config = DatabaseConfig(
            db_type=DatabaseType.MYSQL,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            charset=charset,
        )
        return cls(config, **kwargs)
    
    @classmethod
    def from_env(cls, prefix: str = "", **kwargs) -> "MultiDatabaseConnector":
        """从环境变量创建连接器"""
        config = DatabaseConfig.from_env(prefix)
        return cls(config, **kwargs)
