"""
API Routes - HTTP路由定义

支持两种运行模式:
1. Mock 模式 (默认): 使用模拟数据，适合开发测试
2. 数据库模式: 连接真实 PostgreSQL，通过环境变量配置

v2.0 新增功能:
- 隐私预算管理 API
- 高级隐私机制选择
- 多数据库配置

v3.0 新增功能:
- 审计日志 API
- 性能监控 API
- 分析导出 API

环境变量:
    USE_MOCK_DB: 是否使用 Mock 模式 (默认 "true")
    ENABLE_BUDGET_MANAGEMENT: 是否启用预算管理 (默认 "false")
    DEFAULT_BUDGET: 默认预算值 (默认 "1.0")
    PG_HOST: 数据库主机
    PG_PORT: 数据库端口
    PG_DATABASE: 数据库名
    PG_USER: 用户名
    PG_PASSWORD: 密码
"""
import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from .schemas import QueryRequest, QueryResponse, QueryResponseData, ErrorResponse
from ..core import QueryDriver, QueryContext
from ..budget import PrivacyBudgetManager
from ..audit import AuditLogger, AuditFilter, EventType
from ..performance import PerformanceMonitor, QueryCache, RateLimiter

router = APIRouter(prefix="/api/v1", tags=["Query"])

# 全局实例
_query_driver: QueryDriver = None
_audit_logger: AuditLogger = None
_performance_monitor: PerformanceMonitor = None
_query_cache: QueryCache = None
_rate_limiter: RateLimiter = None


def _use_mock_mode() -> bool:
    """判断是否使用 Mock 模式"""
    use_mock = os.getenv("USE_MOCK_DB", "true").lower()
    return use_mock in ("true", "1", "yes")


def _enable_budget_management() -> bool:
    """判断是否启用预算管理"""
    enable = os.getenv("ENABLE_BUDGET_MANAGEMENT", "false").lower()
    return enable in ("true", "1", "yes")


def _get_default_budget() -> float:
    """获取默认预算值"""
    return float(os.getenv("DEFAULT_BUDGET", "1.0"))


def get_query_driver() -> QueryDriver:
    """
    获取 QueryDriver 实例
    
    根据环境变量 USE_MOCK_DB 决定使用 Mock 还是真实数据库
    """
    global _query_driver
    
    if _query_driver is None:
        enable_budget = _enable_budget_management()
        default_budget = _get_default_budget()
        
        if _use_mock_mode():
            # Mock 模式
            _query_driver = QueryDriver(
                use_mock=True,
                enable_budget_management=enable_budget
            )
            if enable_budget:
                _query_driver.budget_manager = PrivacyBudgetManager(default_budget=default_budget)
            print(f"[API] 使用 Mock 模式启动 (预算管理: {enable_budget})")
        else:
            # 真实数据库模式
            _query_driver = QueryDriver.from_env(
                enable_budget_management=enable_budget
            )
            if enable_budget:
                _query_driver.budget_manager = PrivacyBudgetManager(default_budget=default_budget)
            print(f"[API] 连接数据库: {os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5432')}/{os.getenv('PG_DATABASE', 'postgres')} (预算管理: {enable_budget})")
    
    return _query_driver


def get_audit_logger() -> AuditLogger:
    """获取审计日志记录器 (v3.0)"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器 (v3.0)"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_query_cache() -> QueryCache:
    """获取查询缓存 (v3.0)"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def get_rate_limiter() -> RateLimiter:
    """获取速率限制器 (v3.0)"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


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
        
        # 检查预算不足的情况
        if result.get("error") == "insufficient_budget":
            return QueryResponse(
                status="error",
                data=QueryResponseData(
                    type="BUDGET_ERROR",
                    original_query=request.sql,
                    error=result.get("message"),
                    privacy_info={
                        "remaining_budget": result.get("remaining_budget"),
                        "requested_budget": result.get("requested_budget"),
                    }
                ),
            )
        
        # 构建响应
        response_data = QueryResponseData(
            type=result.get("type", "UNKNOWN"),
            original_query=result.get("original_query", request.sql),
            protected_result=result.get("protected_result"),
            privacy_info=result.get("privacy_info"),
            error=result.get("error"),
        )
        
        # 添加预算状态到响应
        if result.get("budget_status"):
            if response_data.privacy_info is None:
                response_data.privacy_info = {}
            response_data.privacy_info["budget_status"] = result.get("budget_status")
        
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
    - budget_management: 预算管理状态 (v2.0)
    """
    mode = "mock" if _use_mock_mode() else "database"
    budget_enabled = _enable_budget_management()
    
    status = {
        "status": "running",
        "mode": mode,
        "service": "privacy-query-engine",
        "version": "2.0.0",
        "features": {
            "budget_management": budget_enabled,
            "enhanced_sql_analysis": True,
            "advanced_privacy_mechanisms": True,
            "multi_database_support": True,
        }
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


# ==================== v2.0 Budget Management APIs ====================

@router.get(
    "/budget/{user_id}",
    summary="获取用户预算状态",
    description="获取指定用户的隐私预算状态 (v2.0)",
    tags=["Budget"]
)
async def get_budget_status(user_id: str):
    """
    获取用户预算状态
    
    - **user_id**: 用户ID
    
    返回用户的预算状态，包括总预算、已消耗预算、剩余预算等。
    """
    driver = get_query_driver()
    
    if not driver.budget_manager:
        raise HTTPException(
            status_code=400,
            detail="Budget management is not enabled. Set ENABLE_BUDGET_MANAGEMENT=true"
        )
    
    status = driver.get_budget_status(user_id)
    return {
        "status": "success",
        "data": status
    }


@router.post(
    "/budget/{user_id}/reset",
    summary="重置用户预算",
    description="重置指定用户的隐私预算 (v2.0)",
    tags=["Budget"]
)
async def reset_budget(user_id: str):
    """
    重置用户预算
    
    - **user_id**: 用户ID
    
    将用户的已消耗预算重置为0。
    """
    driver = get_query_driver()
    
    if not driver.budget_manager:
        raise HTTPException(
            status_code=400,
            detail="Budget management is not enabled. Set ENABLE_BUDGET_MANAGEMENT=true"
        )
    
    success = driver.reset_user_budget(user_id)
    
    if success:
        return {
            "status": "success",
            "message": f"Budget reset for user {user_id}"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to reset budget")


@router.get(
    "/budget/{user_id}/history",
    summary="获取用户预算历史",
    description="获取指定用户的预算消耗历史 (v2.0)",
    tags=["Budget"]
)
async def get_budget_history(
    user_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="返回记录数量限制")
):
    """
    获取用户预算历史
    
    - **user_id**: 用户ID
    - **limit**: 返回记录数量限制 (默认100)
    
    返回用户的预算消耗历史记录。
    """
    driver = get_query_driver()
    
    if not driver.budget_manager:
        raise HTTPException(
            status_code=400,
            detail="Budget management is not enabled. Set ENABLE_BUDGET_MANAGEMENT=true"
        )
    
    history = driver.budget_manager.get_budget_history(user_id, limit=limit)
    
    return {
        "status": "success",
        "data": {
            "user_id": user_id,
            "transactions": [t.to_dict() for t in history],
            "count": len(history)
        }
    }


# ==================== v3.0 Audit APIs ====================

@router.get(
    "/audit/logs",
    summary="获取审计日志",
    description="获取审计日志列表 (v3.0)",
    tags=["Audit"]
)
async def get_audit_logs(
    user_id: Optional[str] = Query(default=None, description="按用户ID过滤"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回记录数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
):
    """获取审计日志"""
    logger = get_audit_logger()
    
    filter_criteria = AuditFilter(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    
    logs = logger.filter_logs(filter_criteria)
    
    return {
        "status": "success",
        "data": {
            "logs": [log.to_dict() for log in logs],
            "count": len(logs),
        }
    }


@router.get(
    "/audit/statistics",
    summary="获取审计统计",
    description="获取审计统计信息 (v3.0)",
    tags=["Audit"]
)
async def get_audit_statistics():
    """获取审计统计信息"""
    logger = get_audit_logger()
    stats = logger.get_statistics()
    
    return {
        "status": "success",
        "data": stats
    }


@router.get(
    "/audit/export",
    summary="导出审计日志",
    description="导出审计日志为指定格式 (v3.0)",
    tags=["Audit"]
)
async def export_audit_logs(
    format: str = Query(default="json", description="导出格式 (json/csv)"),
    user_id: Optional[str] = Query(default=None, description="按用户ID过滤"),
):
    """导出审计日志"""
    logger = get_audit_logger()
    
    filter_criteria = AuditFilter(user_id=user_id, limit=100000)
    
    if format == "csv":
        content = logger.export_csv(filter_criteria)
        return {"status": "success", "format": "csv", "data": content}
    else:
        content = logger.export_json(filter_criteria)
        return {"status": "success", "format": "json", "data": content}


@router.get(
    "/audit/integrity",
    summary="验证审计日志完整性",
    description="验证审计日志链的完整性 (v3.0)",
    tags=["Audit"]
)
async def verify_audit_integrity():
    """验证审计日志完整性"""
    logger = get_audit_logger()
    is_valid = logger.verify_chain_integrity()
    
    return {
        "status": "success",
        "data": {
            "integrity_valid": is_valid,
            "verified_at": datetime.now().isoformat(),
        }
    }


# ==================== v3.0 Performance APIs ====================

@router.get(
    "/performance/metrics",
    summary="获取性能指标",
    description="获取查询性能指标 (v3.0)",
    tags=["Performance"]
)
async def get_performance_metrics(
    limit: int = Query(default=100, ge=1, le=1000, description="返回记录数量限制"),
):
    """获取性能指标"""
    monitor = get_performance_monitor()
    metrics = monitor.get_metrics(limit=limit)
    
    return {
        "status": "success",
        "data": {
            "metrics": [m.to_dict() for m in metrics],
            "count": len(metrics),
        }
    }


@router.get(
    "/performance/statistics",
    summary="获取性能统计",
    description="获取性能统计信息 (v3.0)",
    tags=["Performance"]
)
async def get_performance_statistics():
    """获取性能统计信息"""
    monitor = get_performance_monitor()
    stats = monitor.get_statistics()
    percentiles = monitor.get_percentiles()
    
    return {
        "status": "success",
        "data": {
            **stats,
            "percentiles": percentiles,
        }
    }


@router.get(
    "/performance/slow-queries",
    summary="获取慢查询",
    description="获取慢查询列表 (v3.0)",
    tags=["Performance"]
)
async def get_slow_queries(
    limit: int = Query(default=100, ge=1, le=1000, description="返回记录数量限制"),
):
    """获取慢查询列表"""
    monitor = get_performance_monitor()
    slow_queries = monitor.get_slow_queries(limit=limit)
    
    return {
        "status": "success",
        "data": {
            "slow_queries": [q.to_dict() for q in slow_queries],
            "count": len(slow_queries),
            "threshold_ms": monitor.slow_query_threshold_ms,
        }
    }


@router.get(
    "/performance/cache",
    summary="获取缓存统计",
    description="获取查询缓存统计信息 (v3.0)",
    tags=["Performance"]
)
async def get_cache_statistics():
    """获取缓存统计信息"""
    cache = get_query_cache()
    stats = cache.get_statistics()
    
    return {
        "status": "success",
        "data": stats
    }


@router.post(
    "/performance/cache/clear",
    summary="清空缓存",
    description="清空查询缓存 (v3.0)",
    tags=["Performance"]
)
async def clear_cache():
    """清空查询缓存"""
    cache = get_query_cache()
    cache.invalidate_all()
    
    return {
        "status": "success",
        "message": "Cache cleared"
    }


@router.get(
    "/performance/rate-limit",
    summary="获取速率限制状态",
    description="获取速率限制统计信息 (v3.0)",
    tags=["Performance"]
)
async def get_rate_limit_status():
    """获取速率限制状态"""
    limiter = get_rate_limiter()
    stats = limiter.get_statistics()
    
    return {
        "status": "success",
        "data": stats
    }


# ==================== v3.0 Status API ====================

@router.get("/status/v3", summary="服务状态 (v3.0)")
async def service_status_v3():
    """
    获取服务详细状态 (v3.0)
    
    返回所有v3.0功能的状态信息
    """
    mode = "mock" if _use_mock_mode() else "database"
    budget_enabled = _enable_budget_management()
    
    # 获取各组件统计
    audit_stats = get_audit_logger().get_statistics()
    perf_stats = get_performance_monitor().get_statistics()
    cache_stats = get_query_cache().get_statistics()
    rate_stats = get_rate_limiter().get_statistics()
    
    status = {
        "status": "running",
        "mode": mode,
        "service": "privacy-query-engine",
        "version": "3.0.0",
        "features": {
            # v2.0 features
            "budget_management": budget_enabled,
            "enhanced_sql_analysis": True,
            "advanced_privacy_mechanisms": True,
            "multi_database_support": True,
            # v3.0 features
            "audit_logging": True,
            "performance_monitoring": True,
            "query_caching": True,
            "rate_limiting": True,
            "distributed_support": True,
            "analytics_integration": True,
        },
        "components": {
            "audit": {
                "total_entries": audit_stats.get("total_entries", 0),
            },
            "performance": {
                "total_queries": perf_stats.get("total_queries", 0),
                "average_time_ms": perf_stats.get("average_time_ms", 0),
            },
            "cache": {
                "entries": cache_stats.get("entries", 0),
                "hit_rate": cache_stats.get("hit_rate", 0),
            },
            "rate_limiter": {
                "total_requests": rate_stats.get("total_requests", 0),
                "rejection_rate": rate_stats.get("rejection_rate", 0),
            },
        }
    }
    
    return status
