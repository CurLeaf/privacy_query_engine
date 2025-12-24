"""
API Schemas - 请求/响应模型
使用 Pydantic 定义数据模型，包含完整的 OpenAPI 元数据
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class QueryRequest(BaseModel):
    """
    查询请求模型
    
    用于提交需要隐私保护的 SQL 查询
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sql": "SELECT COUNT(*) FROM users WHERE age > 18;",
                    "context": {
                        "user_id": "user_001",
                        "session_id": "sess_abc123"
                    }
                },
                {
                    "sql": "SELECT AVG(salary) FROM employees WHERE department = 'Engineering';",
                    "context": {
                        "user_id": "admin_001"
                    }
                },
                {
                    "sql": "SELECT name, email FROM users LIMIT 10;",
                    "context": {
                        "user_id": "user_002",
                        "purpose": "data_export"
                    }
                }
            ]
        }
    )
    
    sql: str = Field(
        ...,
        description="SQL 查询语句。支持 SELECT 聚合查询和包含敏感列的查询。系统会自动分析查询类型并应用相应的隐私保护机制。",
        min_length=1,
        examples=["SELECT COUNT(*) FROM users;", "SELECT AVG(salary) FROM employees;"]
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="查询上下文信息。可包含用户ID、会话ID、查询目的等元数据，用于审计和预算管理。",
        examples=[
            {"user_id": "user_001", "session_id": "sess_123"},
            {"user_id": "admin_001", "purpose": "analytics"}
        ]
    )


class PrivacyInfo(BaseModel):
    """
    隐私信息模型
    
    描述应用的隐私保护机制和参数
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "epsilon": 1.0,
                    "method": "Laplace",
                    "sensitivity": 1,
                    "noise_added": 3
                },
                {
                    "method": "Masking",
                    "columns_processed": ["name", "email", "phone"]
                }
            ]
        }
    )
    
    epsilon: Optional[float] = Field(
        default=None,
        description="差分隐私预算参数 ε。较小的值提供更强的隐私保护，但可能降低数据可用性。",
        gt=0,
        examples=[0.1, 1.0, 10.0]
    )
    
    method: str = Field(
        ...,
        description="隐私保护方法。可能的值：'Laplace'（拉普拉斯机制）、'Gaussian'（高斯机制）、'Masking'（掩码）、'Hashing'（哈希）等。",
        examples=["Laplace", "Gaussian", "Masking", "Hashing"]
    )
    
    sensitivity: Optional[float] = Field(
        default=None,
        description="查询敏感度。表示单个记录的变化对查询结果的最大影响。",
        ge=0,
        examples=[1, 2, 10]
    )
    
    columns_processed: Optional[List[str]] = Field(
        default=None,
        description="经过隐私处理的列名列表。用于去标识化场景。",
        examples=[["name", "email"], ["ssn", "phone", "address"]]
    )


class QueryResponseData(BaseModel):
    """
    查询响应数据模型
    
    包含处理后的查询结果和隐私信息
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "DP",
                    "original_query": "SELECT COUNT(*) FROM users;",
                    "protected_result": 1023,
                    "privacy_info": {
                        "epsilon": 1.0,
                        "method": "Laplace",
                        "sensitivity": 1,
                        "noise_added": 3
                    }
                },
                {
                    "type": "DeID",
                    "original_query": "SELECT name, email FROM users LIMIT 5;",
                    "protected_result": [
                        {"name": "User_***", "email": "***@example.com"},
                        {"name": "User_***", "email": "***@example.com"}
                    ],
                    "privacy_info": {
                        "method": "Masking",
                        "columns_processed": ["name", "email"]
                    }
                }
            ]
        }
    )
    
    type: str = Field(
        ...,
        description="处理类型。'DP'=差分隐私、'DeID'=去标识化、'PASS'=直接通过、'ERROR'=错误",
        examples=["DP", "DeID", "PASS", "ERROR"]
    )
    
    original_query: str = Field(
        ...,
        description="原始 SQL 查询语句",
        examples=["SELECT COUNT(*) FROM users;"]
    )
    
    protected_result: Optional[Any] = Field(
        default=None,
        description="隐私保护后的查询结果。可以是数值、列表、字典等类型，取决于查询类型。",
        examples=[1023, [{"name": "User_***", "email": "***@example.com"}]]
    )
    
    privacy_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="隐私保护信息，包括使用的方法、参数等详细信息。",
        examples=[
            {"epsilon": 1.0, "method": "Laplace", "sensitivity": 1},
            {"method": "Masking", "columns_processed": ["name", "email"]}
        ]
    )
    
    error: Optional[str] = Field(
        default=None,
        description="错误信息（如果处理失败）",
        examples=["SQL syntax error", "Unsupported query type"]
    )


class QueryResponse(BaseModel):
    """
    API 响应模型
    
    标准的 API 响应格式
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "type": "DP",
                        "original_query": "SELECT COUNT(*) FROM users;",
                        "protected_result": 1023,
                        "privacy_info": {
                            "epsilon": 1.0,
                            "method": "Laplace",
                            "sensitivity": 1
                        }
                    }
                },
                {
                    "status": "error",
                    "message": "SQL syntax error",
                    "data": {
                        "type": "ERROR",
                        "original_query": "SELECT COUNT(*) FORM users;",
                        "error": "Unexpected token 'FORM' at position 15"
                    }
                }
            ]
        }
    )
    
    status: str = Field(
        ...,
        description="响应状态。'success'=成功、'error'=失败",
        examples=["success", "error"]
    )
    
    data: Optional[QueryResponseData] = Field(
        default=None,
        description="响应数据，包含查询结果和隐私信息"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="响应消息，通常用于错误情况",
        examples=["Query processed successfully", "Invalid SQL syntax"]
    )


class ErrorResponse(BaseModel):
    """
    标准错误响应模型
    
    统一的错误响应格式，包含错误代码、消息和详细信息
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "error",
                    "error_code": "INVALID_SQL",
                    "message": "SQL 语法错误",
                    "detail": "Unexpected token 'FORM' at position 15",
                    "timestamp": "2024-12-24T10:30:00Z"
                },
                {
                    "status": "error",
                    "error_code": "INSUFFICIENT_BUDGET",
                    "message": "隐私预算不足",
                    "detail": "Requested epsilon: 2.0, Remaining budget: 0.5",
                    "timestamp": "2024-12-24T10:31:00Z"
                },
                {
                    "status": "error",
                    "error_code": "UNSUPPORTED_QUERY",
                    "message": "不支持的查询类型",
                    "detail": "UPDATE operations are not supported",
                    "timestamp": "2024-12-24T10:32:00Z"
                }
            ]
        }
    )
    
    status: str = Field(
        default="error",
        description="响应状态，固定为 'error'",
        examples=["error"]
    )
    
    error_code: str = Field(
        ...,
        description="错误代码。标准错误代码包括：INVALID_SQL, INSUFFICIENT_BUDGET, UNSUPPORTED_QUERY, INTERNAL_ERROR 等",
        examples=["INVALID_SQL", "INSUFFICIENT_BUDGET", "UNSUPPORTED_QUERY", "INTERNAL_ERROR"]
    )
    
    message: str = Field(
        ...,
        description="人类可读的错误消息",
        examples=["SQL 语法错误", "隐私预算不足", "不支持的查询类型"]
    )
    
    detail: Optional[str] = Field(
        default=None,
        description="详细的错误信息，包含具体的错误原因和上下文",
        examples=[
            "Unexpected token 'FORM' at position 15",
            "Requested epsilon: 2.0, Remaining budget: 0.5"
        ]
    )
    
    timestamp: str = Field(
        ...,
        description="错误发生的时间戳（ISO 8601 格式）",
        examples=["2024-12-24T10:30:00Z", "2024-12-24T10:30:00.123456Z"]
    )




# ==================== 预算管理相关模型 ====================

class BudgetStatus(BaseModel):
    """
    预算状态模型
    
    描述用户的隐私预算状态
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "user_001",
                    "total_budget": 10.0,
                    "consumed_budget": 3.5,
                    "remaining_budget": 6.5,
                    "last_updated": "2024-12-24T10:30:00Z"
                }
            ]
        }
    )
    
    user_id: str = Field(
        ...,
        description="用户唯一标识符",
        examples=["user_001", "admin_001"]
    )
    
    total_budget: float = Field(
        ...,
        description="总隐私预算（epsilon 值）",
        gt=0,
        examples=[1.0, 10.0, 100.0]
    )
    
    consumed_budget: float = Field(
        ...,
        description="已消耗的隐私预算",
        ge=0,
        examples=[0.5, 3.5, 8.2]
    )
    
    remaining_budget: float = Field(
        ...,
        description="剩余的隐私预算",
        ge=0,
        examples=[0.5, 6.5, 91.8]
    )
    
    last_updated: str = Field(
        ...,
        description="最后更新时间（ISO 8601 格式）",
        examples=["2024-12-24T10:30:00Z"]
    )


class BudgetTransaction(BaseModel):
    """
    预算交易记录模型
    
    记录单次预算消耗的详细信息
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "transaction_id": "txn_abc123",
                    "user_id": "user_001",
                    "query": "SELECT COUNT(*) FROM users;",
                    "epsilon_consumed": 1.0,
                    "timestamp": "2024-12-24T10:30:00Z",
                    "query_type": "DP"
                }
            ]
        }
    )
    
    transaction_id: str = Field(
        ...,
        description="交易唯一标识符",
        examples=["txn_abc123", "txn_def456"]
    )
    
    user_id: str = Field(
        ...,
        description="用户唯一标识符",
        examples=["user_001", "admin_001"]
    )
    
    query: str = Field(
        ...,
        description="执行的 SQL 查询",
        examples=["SELECT COUNT(*) FROM users;"]
    )
    
    epsilon_consumed: float = Field(
        ...,
        description="本次查询消耗的 epsilon 值",
        gt=0,
        examples=[0.1, 1.0, 2.5]
    )
    
    timestamp: str = Field(
        ...,
        description="交易时间戳（ISO 8601 格式）",
        examples=["2024-12-24T10:30:00Z"]
    )
    
    query_type: Optional[str] = Field(
        default=None,
        description="查询类型",
        examples=["DP", "DeID"]
    )


class BudgetStatusResponse(BaseModel):
    """预算状态响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "user_id": "user_001",
                        "total_budget": 10.0,
                        "consumed_budget": 3.5,
                        "remaining_budget": 6.5,
                        "last_updated": "2024-12-24T10:30:00Z"
                    }
                }
            ]
        }
    )
    
    status: str = Field(
        default="success",
        description="响应状态",
        examples=["success"]
    )
    
    data: BudgetStatus = Field(
        ...,
        description="预算状态数据"
    )


class BudgetHistoryResponse(BaseModel):
    """预算历史响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "user_id": "user_001",
                        "transactions": [
                            {
                                "transaction_id": "txn_abc123",
                                "user_id": "user_001",
                                "query": "SELECT COUNT(*) FROM users;",
                                "epsilon_consumed": 1.0,
                                "timestamp": "2024-12-24T10:30:00Z"
                            }
                        ],
                        "count": 1
                    }
                }
            ]
        }
    )
    
    status: str = Field(
        default="success",
        description="响应状态",
        examples=["success"]
    )
    
    data: Dict[str, Any] = Field(
        ...,
        description="预算历史数据，包含 user_id、transactions 列表和 count"
    )


# ==================== 审计日志相关模型 ====================

class AuditLog(BaseModel):
    """
    审计日志模型
    
    记录系统操作的审计信息
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "log_id": "log_abc123",
                    "user_id": "user_001",
                    "event_type": "QUERY_EXECUTED",
                    "query": "SELECT COUNT(*) FROM users;",
                    "result_type": "DP",
                    "timestamp": "2024-12-24T10:30:00Z",
                    "metadata": {
                        "epsilon": 1.0,
                        "execution_time_ms": 45
                    }
                }
            ]
        }
    )
    
    log_id: str = Field(
        ...,
        description="日志唯一标识符",
        examples=["log_abc123", "log_def456"]
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="用户唯一标识符",
        examples=["user_001", "admin_001"]
    )
    
    event_type: str = Field(
        ...,
        description="事件类型。可能的值：QUERY_EXECUTED, BUDGET_RESET, CACHE_CLEARED 等",
        examples=["QUERY_EXECUTED", "BUDGET_RESET", "CACHE_CLEARED"]
    )
    
    query: Optional[str] = Field(
        default=None,
        description="相关的 SQL 查询（如果适用）",
        examples=["SELECT COUNT(*) FROM users;"]
    )
    
    result_type: Optional[str] = Field(
        default=None,
        description="查询结果类型（如果适用）",
        examples=["DP", "DeID", "PASS"]
    )
    
    timestamp: str = Field(
        ...,
        description="事件时间戳（ISO 8601 格式）",
        examples=["2024-12-24T10:30:00Z"]
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="额外的元数据信息",
        examples=[{"epsilon": 1.0, "execution_time_ms": 45}]
    )


class AuditLogResponse(BaseModel):
    """审计日志响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "logs": [
                            {
                                "log_id": "log_abc123",
                                "user_id": "user_001",
                                "event_type": "QUERY_EXECUTED",
                                "timestamp": "2024-12-24T10:30:00Z"
                            }
                        ],
                        "count": 1
                    }
                }
            ]
        }
    )
    
    status: str = Field(
        default="success",
        description="响应状态",
        examples=["success"]
    )
    
    data: Dict[str, Any] = Field(
        ...,
        description="审计日志数据，包含 logs 列表和 count"
    )


# ==================== 性能监控相关模型 ====================

class PerformanceMetric(BaseModel):
    """
    性能指标模型
    
    记录查询的性能指标
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "metric_id": "metric_abc123",
                    "query": "SELECT COUNT(*) FROM users;",
                    "execution_time_ms": 45.3,
                    "result_size": 1,
                    "timestamp": "2024-12-24T10:30:00Z",
                    "cache_hit": False
                }
            ]
        }
    )
    
    metric_id: str = Field(
        ...,
        description="指标唯一标识符",
        examples=["metric_abc123", "metric_def456"]
    )
    
    query: str = Field(
        ...,
        description="执行的 SQL 查询",
        examples=["SELECT COUNT(*) FROM users;"]
    )
    
    execution_time_ms: float = Field(
        ...,
        description="查询执行时间（毫秒）",
        ge=0,
        examples=[10.5, 45.3, 123.7]
    )
    
    result_size: int = Field(
        ...,
        description="结果集大小（记录数或字节数）",
        ge=0,
        examples=[1, 100, 1000]
    )
    
    timestamp: str = Field(
        ...,
        description="指标记录时间（ISO 8601 格式）",
        examples=["2024-12-24T10:30:00Z"]
    )
    
    cache_hit: Optional[bool] = Field(
        default=None,
        description="是否命中缓存",
        examples=[True, False]
    )


class PerformanceMetricResponse(BaseModel):
    """性能指标响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "metrics": [
                            {
                                "metric_id": "metric_abc123",
                                "query": "SELECT COUNT(*) FROM users;",
                                "execution_time_ms": 45.3,
                                "result_size": 1,
                                "timestamp": "2024-12-24T10:30:00Z"
                            }
                        ],
                        "count": 1
                    }
                }
            ]
        }
    )
    
    status: str = Field(
        default="success",
        description="响应状态",
        examples=["success"]
    )
    
    data: Dict[str, Any] = Field(
        ...,
        description="性能指标数据，包含 metrics 列表和 count"
    )
