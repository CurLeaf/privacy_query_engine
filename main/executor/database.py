"""
DatabaseConnection - 数据库连接管理
使用 SQLModel/SQLAlchemy 连接 PostgreSQL
"""
import os
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from urllib.parse import quote_plus

from sqlmodel import create_engine, Session, text
from sqlalchemy.pool import QueuePool
from sqlalchemy import event


class DatabaseConfig:
    """数据库配置类 - 支持环境变量"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
    ):
        # 优先使用传入参数，否则读取环境变量，最后使用默认值
        self.host = host or os.getenv("PG_HOST", "localhost")
        self.port = port or int(os.getenv("PG_PORT", "5432"))
        self.database = database or os.getenv("PG_DATABASE", "postgres")
        self.user = user or os.getenv("PG_USER", "postgres")
        self.password = password or os.getenv("PG_PASSWORD", "")
    
    def to_connection_string(self, driver: str = "psycopg2") -> str:
        """生成连接字符串"""
        # URL编码密码中的特殊字符
        encoded_password = quote_plus(self.password) if self.password else ""
        
        if driver == "asyncpg":
            return f"postgresql+asyncpg://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql+psycopg2://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"
    
    def __repr__(self):
        return f"DatabaseConfig(host={self.host}, port={self.port}, database={self.database}, user={self.user})"


class DatabaseConnection:
    """数据库连接管理器"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        echo: bool = False,
        **kwargs
    ):
        """
        初始化数据库连接
        
        Args:
            host: 数据库主机 (默认读取 PG_HOST 环境变量)
            port: 端口号 (默认读取 PG_PORT 环境变量)
            database: 数据库名 (默认读取 PG_DATABASE 环境变量)
            user: 用户名 (默认读取 PG_USER 环境变量)
            password: 密码 (默认读取 PG_PASSWORD 环境变量)
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_timeout: 连接池超时时间(秒)
            echo: 是否打印SQL语句
        """
        self.config = DatabaseConfig(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.echo = echo
        self._engine = None
        self._extra_params = kwargs
    
    @property
    def connection_string(self) -> str:
        """获取连接字符串"""
        return self.config.to_connection_string()
    
    @property
    def engine(self):
        """懒加载数据库引擎"""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                echo=self.echo,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_pre_ping=True,  # 自动检测断开的连接
            )
            
            # 添加连接事件监听（可用于调试）
            if self.echo:
                @event.listens_for(self._engine, "connect")
                def on_connect(dbapi_conn, connection_record):
                    print(f"[DB] 新连接建立: {self.config.host}:{self.config.port}/{self.config.database}")
        
        return self._engine
    
    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试数据库连接
        
        Returns:
            包含连接状态和服务器信息的字典
        """
        try:
            with self.get_session() as session:
                # 获取PostgreSQL版本
                result = session.execute(text("SELECT version();"))
                version = result.scalar()
                
                # 获取当前数据库
                result = session.execute(text("SELECT current_database();"))
                current_db = result.scalar()
                
                # 获取当前用户
                result = session.execute(text("SELECT current_user;"))
                current_user = result.scalar()
                
                return {
                    "status": "connected",
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": current_db,
                    "user": current_user,
                    "version": version,
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "host": self.config.host,
                "port": self.config.port,
            }
    
    def execute_query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行查询并返回结果列表
        
        Args:
            sql: SQL查询语句
            params: 查询参数 (用于参数化查询)
            
        Returns:
            查询结果列表 (每行为一个字典)
        """
        with self.get_session() as session:
            if params:
                result = session.execute(text(sql), params)
            else:
                result = session.execute(text(sql))
            
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def execute_scalar(self, sql: str, params: Dict[str, Any] = None) -> Any:
        """
        执行查询并返回单个值
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果 (单个值)
        """
        with self.get_session() as session:
            if params:
                result = session.execute(text(sql), params)
            else:
                result = session.execute(text(sql))
            return result.scalar()
    
    def execute_many(self, sql: str, data: List[Dict[str, Any]]) -> int:
        """
        批量执行SQL语句
        
        Args:
            sql: SQL语句 (INSERT/UPDATE/DELETE)
            data: 参数列表
            
        Returns:
            影响的行数
        """
        with self.get_session() as session:
            result = session.execute(text(sql), data)
            return result.rowcount
    
    def get_tables(self) -> List[str]:
        """获取当前数据库的所有表名"""
        sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        result = self.execute_query(sql)
        return [row["table_name"] for row in result]
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表的列信息
        
        Args:
            table_name: 表名
            
        Returns:
            列信息列表
        """
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
        return self.execute_query(sql, {"table_name": table_name})
    
    def close(self):
        """关闭数据库连接池"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            print(f"[DB] 连接池已关闭: {self.config.host}:{self.config.port}")
    
    def __enter__(self):
        """支持 with 语句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭连接"""
        self.close()
    
    @classmethod
    def from_url(cls, url: str, **kwargs) -> "DatabaseConnection":
        """
        从连接URL创建实例
        
        Args:
            url: PostgreSQL连接URL
            
        Returns:
            DatabaseConnection实例
        """
        conn = cls(**kwargs)
        conn.config = DatabaseConfig()  # 创建空配置
        conn._connection_string_override = url
        return conn
    
    @classmethod
    def from_env(cls, **kwargs) -> "DatabaseConnection":
        """
        从环境变量创建实例
        
        环境变量:
            PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
            
        Returns:
            DatabaseConnection实例
        """
        return cls(**kwargs)
