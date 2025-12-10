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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router, get_query_driver, reset_query_driver


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
    app = FastAPI(
        title="Privacy Query Engine",
        description="""
## 差分隐私与去标识化查询引擎 API

### 功能
- 对 SQL 查询自动应用隐私保护
- 支持差分隐私 (DP) 和去标识化 (DeID) 两种保护方式
- 根据策略配置自动选择保护方式

### 运行模式
- **Mock 模式**: 使用模拟数据（默认）
- **数据库模式**: 连接真实 PostgreSQL 数据库

### 环境变量
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `USE_MOCK_DB` | 是否使用 Mock 模式 | `true` |
| `PG_HOST` | 数据库主机 | `localhost` |
| `PG_PORT` | 数据库端口 | `5432` |
| `PG_DATABASE` | 数据库名 | `postgres` |
| `PG_USER` | 用户名 | `postgres` |
| `PG_PASSWORD` | 密码 | - |
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
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
            "version": "1.0.0",
            "mode": _get_run_mode(),
            "docs": "/docs",
            "status": "/api/v1/status",
        }
    
    return app


# 用于直接运行: uvicorn main.api.server:app
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
