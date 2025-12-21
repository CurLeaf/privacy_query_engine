# Executor module - 能力域4: 查询执行与结果封装
from .query_executor import QueryExecutor, QueryResult, ExecutionMode
from .database import DatabaseConnection, DatabaseConfig
from .mock import MockDatabaseExecutor
from .multi_database import (
    MultiDatabaseConnector,
    DatabaseType,
    DatabaseConfig as MultiDatabaseConfig,
    ConnectionPoolConfig,
    RetryConfig,
    SchemaChange,
    ConnectionError
)

__all__ = [
    "QueryExecutor",
    "QueryResult", 
    "ExecutionMode",
    "DatabaseConnection",
    "DatabaseConfig",
    "MockDatabaseExecutor",
    "MultiDatabaseConnector",
    "DatabaseType",
    "MultiDatabaseConfig",
    "ConnectionPoolConfig",
    "RetryConfig",
    "SchemaChange",
    "ConnectionError",
]

