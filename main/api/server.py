"""
FastAPI Server - HTTP服务入口

启动方式:
    # Mock 模式 (默认)
    uvicorn main.api.server:app --reload --port 8000
    
    # 数据库模式
    USE_MOCK_DB=false PG_HOST=localhost PG_DATABASE=privacy PG_USER=postgres PG_PASSWORD=123456 uvicorn main.api.server:app --reload --port 8000
    
    # Windows PowerShell
    $env:USE_MOCK_DB="false"; $env:PG_HOST="localhost"; $env:PG_DATABASE="privacy"; $env:PG_USER="postgres"; $env:PG_PASSWORD="123456"; uvicorn main.api.server:app --reload --port 8000
"""
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .routes import router, get_query_driver, reset_query_driver
from .openapi_config import OpenAPIConfig


def _get_run_mode() -> str:
    """获取运行模式"""
    use_mock = os.getenv("USE_MOCK_DB", "true").lower()
    return "mock" if use_mock in ("true", "1", "yes") else "database"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    mode = _get_run_mode()
    print("=" * 50)
    print("🚀 Privacy Query Engine 启动中...")
    print(f"📋 运行模式: {mode.upper()}")
    
    if mode == "database":
        print(f"🔌 数据库: {os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5432')}/{os.getenv('PG_DATABASE', 'postgres')}")
    
    print("=" * 50)
    
    # 预初始化 QueryDriver
    try:
        driver = get_query_driver()
        if mode == "database":
            status = driver.test_connection()
            if status.get("status") == "connected":
                print(f"✅ 数据库连接成功: {status.get('database')}")
            else:
                print(f"⚠️ 数据库连接失败: {status.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"⚠️ 初始化警告: {e}")
    
    yield
    
    # 关闭时
    print("🛑 Privacy Query Engine 关闭中...")
    reset_query_driver()
    print("✅ 资源已释放")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    # 获取 OpenAPI 元数据
    metadata = OpenAPIConfig.get_metadata()
    
    app = FastAPI(
        title=metadata["title"],
        version=metadata["version"],
        description=metadata["description"],
        contact=metadata["contact"],
        license_info=metadata["license"],
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        openapi_tags=OpenAPIConfig.get_tags_metadata(),
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(router)
    
    # 根路径
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "Privacy Query Engine",
            "version": metadata["version"],
            "mode": _get_run_mode(),
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "status": "/api/v1/status",
        }
    
    # 自定义 OpenAPI schema
    def custom_openapi() -> Dict[str, Any]:
        """
        自定义 OpenAPI schema 生成
        
        添加额外的元数据、服务器信息、安全方案等
        """
        if app.openapi_schema:
            return app.openapi_schema
        
        # 生成基础 OpenAPI schema
        openapi_schema = get_openapi(
            title=metadata["title"],
            version=metadata["version"],
            description=metadata["description"],
            routes=app.routes,
            tags=OpenAPIConfig.get_tags_metadata(),
        )
        
        # 添加联系信息和许可证
        openapi_schema["info"]["contact"] = metadata["contact"]
        openapi_schema["info"]["license"] = metadata["license"]
        
        # 添加服务器列表
        openapi_schema["servers"] = OpenAPIConfig.get_servers()
        
        # 添加外部文档链接
        openapi_schema["externalDocs"] = OpenAPIConfig.get_external_docs()
        
        # 添加安全方案（可选）
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        openapi_schema["components"]["securitySchemes"] = OpenAPIConfig.get_security_schemes()
        
        # 缓存 schema
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    # 绑定自定义 OpenAPI 函数
    app.openapi = custom_openapi
    
    return app


# 用于直接运行: uvicorn main.api.server:app
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
