"""
FastAPI Server - HTTP服务入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="Privacy Query Engine",
        description="差分隐私与去标识化查询引擎 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
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
            "docs": "/docs",
        }
    
    return app


# 用于直接运行: uvicorn main.api.server:app
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

