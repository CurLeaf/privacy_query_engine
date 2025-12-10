"""
API Routes - HTTP路由定义

支持两种运行模式:
1. Mock 模式 (默认): 使用模拟数据，适合开发测试
2. 数据库模式: 连接真实 PostgreSQL，通过环境变量配置

环境变量:
    USE_MOCK_DB: 是否使用 Mock 模式 (默认 "true")
    PG_HOST: 数据库主机
    PG_PORT: 数据库端口
    PG_DATABASE: 数据库名
    PG_USER: 用户名
    PG_PASSWORD: 密码
"""
import os
from fastapi import APIRouter, HTTPException

from .schemas import QueryRequest, QueryResponse, QueryResponseData, ErrorResponse
from ..core import QueryDriver, QueryContext

router = APIRouter(prefix="/api/v1", tags=["Query"])

# 全局 QueryDriver 实例
_query_driver: QueryDriver = None


def _use_mock_mode() -> bool:
    """判断是否使用 Mock 模式"""
    use_mock = os.getenv("USE_MOCK_DB", "true").lower()
    return use_mock in ("true", "1", "yes")


def get_query_driver() -> QueryDriver:
    """
    获取 QueryDriver 实例
    
    根据环境变量 USE_MOCK_DB 决定使用 Mock 还是真实数据库
    """
    global _query_driver
    
    if _query_driver is None:
        if _use_mock_mode():
            # Mock 模式
            _query_driver = QueryDriver(use_mock=True)
            print("[API] 使用 Mock 模式启动")
        else:
            # 真实数据库模式
            _query_driver = QueryDriver.from_env()
            print(f"[API] 连接数据库: {os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5432')}/{os.getenv('PG_DATABASE', 'postgres')}")
    
    return _query_driver


def reset_query_driver():
    """重置 QueryDriver 实例（用于测试）"""
    global _query_driver
    if _query_driver is not None:
        _query_driver.close()
        _query_driver = None


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


@router.get("/status", summary="服务状态")
async def service_status():
    """
    获取服务详细状态
    
    返回:
    - mode: 运行模式 (mock/database)
    - database: 数据库连接状态 (仅数据库模式)
    """
    mode = "mock" if _use_mock_mode() else "database"
    
    status = {
        "status": "running",
        "mode": mode,
        "service": "privacy-query-engine",
        "version": "1.0.0",
    }
    
    # 如果是数据库模式，检查连接状态
    if not _use_mock_mode():
        try:
            driver = get_query_driver()
            db_status = driver.test_connection()
            status["database"] = {
                "status": db_status.get("status", "unknown"),
                "host": db_status.get("host"),
                "port": db_status.get("port"),
                "database": db_status.get("database"),
            }
        except Exception as e:
            status["database"] = {
                "status": "error",
                "error": str(e),
            }
    
    return status
