"""
OpenAPI 配置模块

提供 OpenAPI 规范的元数据、服务器信息和标签定义
"""
import os
from typing import Dict, Any, List


class OpenAPIConfig:
    """OpenAPI 配置管理器"""
    
    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """
        获取 API 元数据
        
        Returns:
            包含 title, version, description, contact, license 的字典
        """
        return {
            "title": "Privacy Query Engine API",
            "version": "3.0.0",
            "description": """
## 差分隐私与去标识化查询引擎 API

Privacy Query Engine 是一个强大的隐私保护查询系统，自动为 SQL 查询应用差分隐私或去标识化保护。

### 核心功能

- **自动隐私保护**: 根据查询类型自动选择合适的隐私保护机制
- **差分隐私 (DP)**: 对聚合查询添加校准噪声，提供数学上的隐私保证
- **去标识化 (DeID)**: 对包含敏感信息的查询结果进行脱敏处理
- **预算管理**: 跟踪和管理用户的隐私预算消耗
- **审计日志**: 完整的操作审计和日志记录
- **性能监控**: 实时查询性能监控和优化

### 运行模式

- **Mock 模式**: 使用模拟数据，适合开发和测试（默认）
- **数据库模式**: 连接真实 PostgreSQL 数据库

### 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `USE_MOCK_DB` | 是否使用 Mock 模式 | `true` |
| `ENABLE_BUDGET_MANAGEMENT` | 是否启用预算管理 | `false` |
| `DEFAULT_BUDGET` | 默认隐私预算 | `1.0` |
| `PG_HOST` | 数据库主机 | `localhost` |
| `PG_PORT` | 数据库端口 | `5432` |
| `PG_DATABASE` | 数据库名 | `postgres` |
| `PG_USER` | 数据库用户名 | `postgres` |
| `PG_PASSWORD` | 数据库密码 | - |

### 快速开始

1. **启动服务**（Mock 模式）:
   ```bash
   uvicorn main.api.server:app --reload --port 8000
   ```

2. **发送查询请求**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/protect-query" \\
        -H "Content-Type: application/json" \\
        -d '{"sql": "SELECT COUNT(*) FROM users;"}'
   ```

3. **查看交互式文档**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### 技术栈

- **框架**: FastAPI 0.115+
- **数据验证**: Pydantic 2.11+
- **数据库**: PostgreSQL (可选)
- **隐私技术**: 差分隐私、去标识化

### 相关链接

- [GitHub 仓库](https://github.com/curleaf/privacy-query-engine)
- [完整文档](https://github.com/curleaf/privacy-query-engine/blob/main/README.md)
- [问题反馈](https://github.com/curleaf/privacy-query-engine/issues)
            """,
            "contact": {
                "name": "Privacy Query Engine Team",
                "email": "qbt2587496@gmail.com",
                "url": "https://github.com/curleaf/privacy-query-engine"
            },
            "license": {
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            }
        }
    
    @staticmethod
    def get_servers() -> List[Dict[str, str]]:
        """
        获取服务器列表
        
        Returns:
            服务器配置列表，每个服务器包含 url 和 description
        """
        # 从环境变量获取服务器配置，或使用默认值
        servers = [
            {
                "url": "http://localhost:8000",
                "description": "本地开发服务器"
            }
        ]
        
        # 如果配置了生产环境 URL，添加到列表
        prod_url = os.getenv("PRODUCTION_URL")
        if prod_url:
            servers.append({
                "url": prod_url,
                "description": "生产环境"
            })
        
        # 如果配置了测试环境 URL，添加到列表
        staging_url = os.getenv("STAGING_URL")
        if staging_url:
            servers.append({
                "url": staging_url,
                "description": "测试环境"
            })
        
        return servers
    
    @staticmethod
    def get_tags_metadata() -> List[Dict[str, Any]]:
        """
        获取标签元数据
        
        Returns:
            标签配置列表，每个标签包含 name, description 和可选的 externalDocs
        """
        return [
            {
                "name": "Query",
                "description": """
                    **隐私查询接口**
                    
                    核心查询处理接口，自动应用隐私保护机制。支持：
                    - SQL 查询分析
                    - 差分隐私保护
                    - 去标识化处理
                    - 查询结果返回
                """
            },
            {
                "name": "Budget",
                "description": """
                    **隐私预算管理接口**
                    
                    管理用户的隐私预算消耗。功能包括：
                    - 查询预算状态
                    - 重置用户预算
                    - 查看预算历史
                    - 预算消耗追踪
                """
            },
            {
                "name": "Audit",
                "description": """
                    **审计日志接口**
                    
                    提供完整的操作审计和日志查询。支持：
                    - 日志查询和过滤
                    - 审计统计信息
                    - 日志导出（JSON/CSV）
                    - 日志完整性验证
                """
            },
            {
                "name": "Performance",
                "description": """
                    **性能监控接口**
                    
                    实时监控系统性能和查询效率。包括：
                    - 性能指标收集
                    - 慢查询分析
                    - 缓存统计
                    - 速率限制状态
                """
            },
            {
                "name": "Privacy",
                "description": """
                    **隐私保护机制**
                    
                    与隐私保护相关的接口和功能
                """
            },
            {
                "name": "Root",
                "description": """
                    **根路径和健康检查**
                    
                    基础接口，包括：
                    - 服务信息
                    - 健康检查
                    - 状态查询
                """
            }
        ]
    
    @staticmethod
    def get_external_docs() -> Dict[str, str]:
        """
        获取外部文档链接
        
        Returns:
            包含 description 和 url 的字典
        """
        return {
            "description": "完整的项目文档和使用指南",
            "url": "https://github.com/curleaf/privacy-query-engine/blob/main/README.md"
        }
    
    @staticmethod
    def get_security_schemes() -> Dict[str, Any]:
        """
        获取安全方案定义（可选）
        
        Returns:
            安全方案配置字典
        """
        return {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API 密钥认证（可选）。在请求头中添加 X-API-Key 字段"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Bearer Token 认证（可选）"
            }
        }
