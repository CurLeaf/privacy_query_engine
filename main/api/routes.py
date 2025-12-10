"""
API Routes - HTTP路由定义
"""
from fastapi import APIRouter, HTTPException

from .schemas import QueryRequest, QueryResponse, QueryResponseData, ErrorResponse
from ..core import QueryDriver, QueryContext

router = APIRouter(prefix="/api/v1", tags=["Query"])

# 全局QueryDriver实例
_query_driver: QueryDriver = None


def get_query_driver() -> QueryDriver:
    """获取QueryDriver实例"""
    global _query_driver
    if _query_driver is None:
        _query_driver = QueryDriver()
    return _query_driver


@router.post(
    "/protect-query",
    response_model=QueryResponse,
    summary="保护查询",
    description="对SQL查询应用差分隐私或去标识化保护",
    responses={
        200: {"description": "成功返回隐私保护后的结果"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        422: {"model": ErrorResponse, "description": "不支持的查询类型"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
    }
)
async def protect_query(request: QueryRequest) -> QueryResponse:
    """
    保护查询接口
    
    - **sql**: SQL查询语句
    - **context**: 可选的查询上下文信息
    
    返回经过隐私保护处理的查询结果。
    """
    try:
        driver = get_query_driver()
        
        # 构建查询上下文
        context = None
        if request.context:
            context = QueryContext(
                user_id=request.context.get("user_id"),
                extra=request.context,
            )
        
        # 处理查询
        result = driver.process_query(request.sql, context)
        
        # 构建响应
        response_data = QueryResponseData(
            type=result.get("type", "UNKNOWN"),
            original_query=result.get("original_query", request.sql),
            protected_result=result.get("protected_result"),
            privacy_info=result.get("privacy_info"),
            error=result.get("error"),
        )
        
        return QueryResponse(
            status="success",
            data=response_data,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "privacy-query-engine"}

