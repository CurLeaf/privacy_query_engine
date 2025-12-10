"""
API Schemas - 请求/响应模型
使用 Pydantic 定义数据模型
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """查询请求模型"""
    sql: str = Field(..., description="SQL查询语句", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="查询上下文")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT COUNT(*) FROM users;",
                "context": {"user_id": "user_001"}
            }
        }


class PrivacyInfo(BaseModel):
    """隐私信息模型"""
    epsilon: Optional[float] = Field(default=None, description="隐私预算参数")
    method: str = Field(..., description="隐私保护方法")
    sensitivity: Optional[float] = Field(default=None, description="查询敏感度")
    columns_processed: Optional[List[str]] = Field(default=None, description="处理的列")


class QueryResponseData(BaseModel):
    """查询响应数据模型"""
    type: str = Field(..., description="处理类型: DP/DeID/PASS/ERROR")
    original_query: str = Field(..., description="原始查询")
    protected_result: Optional[Any] = Field(default=None, description="隐私保护后的结果")
    privacy_info: Optional[Dict[str, Any]] = Field(default=None, description="隐私信息")
    error: Optional[str] = Field(default=None, description="错误信息")


class QueryResponse(BaseModel):
    """API响应模型"""
    status: str = Field(..., description="响应状态: success/error")
    data: Optional[QueryResponseData] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="响应消息")
    
    class Config:
        json_schema_extra = {
            "example": {
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
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    status: str = Field(default="error")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(default=None, description="详细信息")

