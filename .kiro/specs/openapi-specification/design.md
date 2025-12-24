# Design Document: OpenAPI Specification

## Overview

本设计文档描述了如何为差分隐私与去标识化查询引擎实现标准的 OpenAPI 规范。该系统已经使用 FastAPI 框架构建，FastAPI 原生支持 OpenAPI 规范生成。本设计将增强现有的 API 文档，使其完全符合 OpenAPI 3.0+ 标准，并提供丰富的元数据、示例和交互式文档。

### Design Goals

1. **标准合规性**: 生成完全符合 OpenAPI 3.0.3 标准的规范文档
2. **完整性**: 包含所有端点、模型、错误响应的完整定义
3. **可用性**: 提供清晰的描述、示例和交互式测试界面
4. **可维护性**: 使用声明式方式定义，易于更新和扩展
5. **集成友好**: 支持导出标准格式，可集成到各种工具链

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  OpenAPI Config  │      │  API Metadata    │            │
│  │  - Title         │      │  - Contact Info  │            │
│  │  - Version       │      │  - License       │            │
│  │  - Description   │      │  - Servers       │            │
│  └──────────────────┘      └──────────────────┘            │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Enhanced Route Definitions               │  │
│  │  - Summary & Description                              │  │
│  │  - Request/Response Models                            │  │
│  │  - Status Codes & Error Responses                     │  │
│  │  - Examples & Tags                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Pydantic Schema Models                   │  │
│  │  - Field Descriptions                                 │  │
│  │  - Validation Rules                                   │  │
│  │  - Examples                                           │  │
│  │  - Nested Models                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │      OpenAPI Specification            │
        │  ┌─────────────────────────────────┐  │
        │  │  /openapi.json (JSON format)    │  │
        │  └─────────────────────────────────┘  │
        │  ┌─────────────────────────────────┐  │
        │  │  /docs (Swagger UI)             │  │
        │  └─────────────────────────────────┘  │
        │  ┌─────────────────────────────────┐  │
        │  │  /redoc (ReDoc UI)              │  │
        │  └─────────────────────────────────┘  │
        └───────────────────────────────────────┘
```

### Component Responsibilities

1. **OpenAPI Config**: 配置 FastAPI 应用的基本元数据
2. **API Metadata**: 定义联系信息、许可证、服务器列表
3. **Enhanced Route Definitions**: 为每个路由添加详细的 OpenAPI 注解
4. **Pydantic Schema Models**: 定义所有数据模型的结构和验证规则
5. **OpenAPI Specification**: 自动生成的标准规范文档

## Components and Interfaces

### 1. OpenAPI Configuration Module

**Location**: `main/api/openapi_config.py`

**Purpose**: 集中管理 OpenAPI 相关的配置和元数据

**Interface**:
```python
class OpenAPIConfig:
    """OpenAPI 配置管理器"""
    
    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """获取 API 元数据"""
        return {
            "title": "Privacy Query Engine API",
            "version": "3.0.0",
            "description": "...",
            "contact": {...},
            "license": {...},
        }
    
    @staticmethod
    def get_servers() -> List[Dict[str, str]]:
        """获取服务器列表"""
        return [
            {"url": "http://localhost:8000", "description": "Development"},
            {"url": "https://api.example.com", "description": "Production"},
        ]
    
    @staticmethod
    def get_tags_metadata() -> List[Dict[str, str]]:
        """获取标签元数据"""
        return [
            {"name": "Query", "description": "隐私查询相关接口"},
            {"name": "Budget", "description": "预算管理接口"},
            ...
        ]
    
    @staticmethod
    def customize_openapi_schema(app: FastAPI) -> Dict[str, Any]:
        """自定义 OpenAPI schema"""
        # 添加额外的元数据和扩展
        pass
```

### 2. Enhanced Schema Models

**Location**: `main/api/schemas.py` (增强现有文件)

**Purpose**: 为所有数据模型添加完整的 OpenAPI 元数据

**Enhancements**:
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List

class QueryRequest(BaseModel):
    """查询请求模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sql": "SELECT COUNT(*) FROM users WHERE age > 18;",
                    "context": {
                        "user_id": "user_001",
                        "session_id": "sess_123"
                    }
                },
                {
                    "sql": "SELECT AVG(salary) FROM employees;",
                    "context": {"user_id": "admin_001"}
                }
            ]
        }
    )
    
    sql: str = Field(
        ...,
        description="SQL 查询语句，支持 SELECT 聚合查询",
        min_length=1,
        examples=["SELECT COUNT(*) FROM users;"]
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="查询上下文信息，包含用户ID、会话ID等元数据",
        examples=[{"user_id": "user_001", "session_id": "sess_123"}]
    )

class ErrorResponse(BaseModel):
    """标准错误响应模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "error",
                    "error_code": "INVALID_SQL",
                    "message": "SQL 语法错误",
                    "detail": "Unexpected token 'FORM' at position 15",
                    "timestamp": "2024-12-24T10:30:00Z"
                }
            ]
        }
    )
    
    status: str = Field(default="error", description="响应状态")
    error_code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(default=None, description="详细错误信息")
    timestamp: str = Field(..., description="错误发生时间 (ISO 8601)")
```

### 3. Enhanced Route Definitions

**Location**: `main/api/routes.py` (增强现有文件)

**Purpose**: 为每个路由添加完整的 OpenAPI 注解

**Enhancements**:
```python
from fastapi import APIRouter, HTTPException, Query, status
from typing import Annotated

@router.post(
    "/protect-query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="执行隐私保护查询",
    description="""
    对 SQL 查询应用差分隐私或去标识化保护。
    
    系统会自动分析查询类型，并根据策略配置选择合适的隐私保护机制：
    - **差分隐私 (DP)**: 对聚合查询添加噪声
    - **去标识化 (DeID)**: 对包含敏感列的查询进行脱敏
    - **直接通过 (PASS)**: 对不涉及隐私的查询直接执行
    
    ## 使用示例
    
    ### 聚合查询（应用差分隐私）
    ```json
    {
      "sql": "SELECT COUNT(*) FROM users WHERE age > 18;",
      "context": {"user_id": "user_001"}
    }
    ```
    
    ### 包含敏感列的查询（应用去标识化）
    ```json
    {
      "sql": "SELECT name, email FROM users LIMIT 10;",
      "context": {"user_id": "user_001"}
    }
    ```
    """,
    responses={
        200: {
            "description": "成功返回隐私保护后的结果",
            "content": {
                "application/json": {
                    "examples": {
                        "dp_query": {
                            "summary": "差分隐私查询示例",
                            "value": {
                                "status": "success",
                                "data": {
                                    "type": "DP",
                                    "original_query": "SELECT COUNT(*) FROM users;",
                                    "protected_result": 1023,
                                    "privacy_info": {
                                        "epsilon": 1.0,
                                        "method": "Laplace",
                                        "sensitivity": 1,
                                        "noise_added": 3
                                    }
                                }
                            }
                        },
                        "deid_query": {
                            "summary": "去标识化查询示例",
                            "value": {
                                "status": "success",
                                "data": {
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
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "error_code": "INVALID_REQUEST",
                        "message": "SQL 查询不能为空",
                        "timestamp": "2024-12-24T10:30:00Z"
                    }
                }
            }
        },
        422: {
            "description": "不支持的查询类型",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "error_code": "UNSUPPORTED_QUERY",
                        "message": "不支持 UPDATE 操作",
                        "detail": "系统仅支持 SELECT 查询",
                        "timestamp": "2024-12-24T10:30:00Z"
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误",
            "model": ErrorResponse
        }
    },
    tags=["Query", "Privacy"]
)
async def protect_query(request: QueryRequest) -> QueryResponse:
    """执行隐私保护查询"""
    # Implementation...
    pass
```

### 4. OpenAPI Schema Customization

**Location**: `main/api/server.py` (增强现有文件)

**Purpose**: 自定义 OpenAPI schema 生成

**Implementation**:
```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    """自定义 OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Privacy Query Engine API",
        version="3.0.0",
        description=OpenAPIConfig.get_metadata()["description"],
        routes=app.routes,
        tags=OpenAPIConfig.get_tags_metadata(),
    )
    
    # 添加服务器信息
    openapi_schema["servers"] = OpenAPIConfig.get_servers()
    
    # 添加安全方案（如果需要）
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # 添加额外的元数据
    openapi_schema["info"]["contact"] = {
        "name": "Privacy Query Engine Team",
        "email": "support@example.com",
        "url": "https://github.com/curleaf/privacy-query-engine"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # 添加外部文档链接
    openapi_schema["externalDocs"] = {
        "description": "完整文档",
        "url": "https://docs.example.com"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 5. Export Utilities

**Location**: `main/api/export.py` (新文件)

**Purpose**: 提供 OpenAPI 规范导出功能

**Interface**:
```python
import json
import yaml
from typing import Dict, Any

class OpenAPIExporter:
    """OpenAPI 规范导出工具"""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    def export_json(self, output_path: str) -> None:
        """导出为 JSON 格式"""
        schema = self.app.openapi()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
    
    def export_yaml(self, output_path: str) -> None:
        """导出为 YAML 格式"""
        schema = self.app.openapi()
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(schema, f, default_flow_style=False, allow_unicode=True)
    
    def get_schema(self) -> Dict[str, Any]:
        """获取 OpenAPI schema 字典"""
        return self.app.openapi()
```

## Data Models

### Core Request/Response Models

```python
# 查询请求
class QueryRequest(BaseModel):
    sql: str
    context: Optional[Dict[str, Any]] = None

# 查询响应
class QueryResponse(BaseModel):
    status: str  # "success" | "error"
    data: Optional[QueryResponseData] = None
    message: Optional[str] = None

class QueryResponseData(BaseModel):
    type: str  # "DP" | "DeID" | "PASS" | "ERROR"
    original_query: str
    protected_result: Optional[Any] = None
    privacy_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 错误响应
class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    detail: Optional[str] = None
    timestamp: str

# 预算相关
class BudgetStatus(BaseModel):
    user_id: str
    total_budget: float
    consumed_budget: float
    remaining_budget: float
    last_updated: str

class BudgetTransaction(BaseModel):
    transaction_id: str
    user_id: str
    query: str
    epsilon_consumed: float
    timestamp: str

# 审计日志
class AuditLog(BaseModel):
    log_id: str
    user_id: Optional[str]
    event_type: str
    query: Optional[str]
    result_type: Optional[str]
    timestamp: str
    metadata: Optional[Dict[str, Any]]

# 性能指标
class PerformanceMetric(BaseModel):
    metric_id: str
    query: str
    execution_time_ms: float
    result_size: int
    timestamp: str
```

### OpenAPI Metadata Models

```python
class APIInfo(BaseModel):
    """API 基本信息"""
    title: str
    version: str
    description: str
    contact: Dict[str, str]
    license: Dict[str, str]

class ServerInfo(BaseModel):
    """服务器信息"""
    url: str
    description: str

class TagMetadata(BaseModel):
    """标签元数据"""
    name: str
    description: str
    externalDocs: Optional[Dict[str, str]] = None
```

## Data Models

### Enhanced Schema Definitions

所有 Pydantic 模型将包含以下增强：

1. **Field 描述**: 每个字段都有清晰的描述
2. **验证规则**: 使用 Pydantic 验证器定义约束
3. **示例值**: 提供多个实际使用示例
4. **默认值**: 为可选字段提供合理的默认值
5. **类型注解**: 使用精确的类型提示

### Model Organization

```
main/api/schemas/
├── __init__.py
├── requests.py      # 请求模型
├── responses.py     # 响应模型
├── errors.py        # 错误模型
├── budget.py        # 预算相关模型
├── audit.py         # 审计相关模型
└── performance.py   # 性能相关模型
```



## Correctness Properties

*属性（Property）是系统在所有有效执行中应该保持为真的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### Property 1: OpenAPI 标准合规性

*对于任何* 生成的 OpenAPI 文档，该文档应该通过 OpenAPI 3.0+ 规范验证器的验证，并包含所有必需的顶层字段（openapi、info、paths）。

**Validates: Requirements 1.1**

### Property 2: 端点完整性

*对于任何* 在 FastAPI 应用中注册的路由集合，生成的 OpenAPI 文档应该在 paths 部分包含所有路由的定义，且路由数量应该匹配。

**Validates: Requirements 1.3**

### Property 3: 文档元数据完整性

*对于任何* 生成的 OpenAPI 文档，info 部分应该包含 title、version、description 字段，且 contact 和 license 信息应该存在。

**Validates: Requirements 1.4, 1.5**

### Property 4: 端点文档完整性

*对于任何* 定义的 API 端点，OpenAPI 文档中该端点应该包含 summary、description、responses（至少一个成功状态码）、以及所有参数的完整定义（包括 type、required、description）。

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 5: 响应示例存在性

*对于任何* 定义的 API 端点，至少一个响应状态码应该包含 example 或 examples 字段。

**Validates: Requirements 2.5**

### Property 6: 数据模型完整性

*对于任何* 使用的 Pydantic 模型，生成的 schema 应该包含所有字段的 type 和 description，required 数组应该正确列出必需字段，且应该包含至少一个 example。

**Validates: Requirements 3.2, 3.3, 3.5**

### Property 7: 嵌套模型引用正确性

*对于任何* 包含嵌套 Pydantic 模型的数据结构，生成的 schema 应该正确使用 $ref 引用子模型或提供内联定义，且所有引用的模型都应该在 components/schemas 中定义。

**Validates: Requirements 3.4**

### Property 8: 错误响应一致性

*对于任何* 错误响应（4xx 或 5xx 状态码），响应应该使用统一的 ErrorResponse 模型结构，包含 status、error_code、message 字段，且在 OpenAPI 文档中有相应的定义和示例。

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 9: API 版本路径前缀

*对于任何* 注册的 API 路由，路径应该包含版本前缀（如 /api/v1），且 OpenAPI 文档的 info.version 字段应该存在且非空。

**Validates: Requirements 5.1, 5.2**

### Property 10: 多版本支持

*对于任何* 定义了多个版本前缀的路由集合（如 /api/v1 和 /api/v2），应用应该能够同时处理来自不同版本的请求而不冲突。

**Validates: Requirements 5.5**

### Property 11: 安全方案定义

*对于任何* 使用认证的 API，OpenAPI 文档应该在 components.securitySchemes 中定义认证方案，且需要认证的端点应该在其 security 字段中声明。

**Validates: Requirements 6.1, 6.3**

### Property 12: 标签组织完整性

*对于任何* 定义的 API 端点，应该至少有一个 tag，且所有使用的 tag 都应该在 OpenAPI 文档的 tags 部分有对应的描述定义。

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

### Property 13: JSON 导出有效性

*对于任何* 生成的 OpenAPI 文档，导出为 JSON 格式后应该是有效的 JSON，且可以被 json.loads() 解析，解析后的对象应该包含所有原始的 OpenAPI 字段。

**Validates: Requirements 9.1**

### Property 14: YAML 导出有效性

*对于任何* 生成的 OpenAPI 文档，导出为 YAML 格式后应该是有效的 YAML，且可以被 yaml.safe_load() 解析，解析后的对象应该与 JSON 导出的内容等价。

**Validates: Requirements 9.2**

### Property 15: OpenAPI 工具兼容性

*对于任何* 导出的 OpenAPI 文档（JSON 或 YAML），应该能够通过 openapi-spec-validator 的验证而不产生错误。

**Validates: Requirements 9.3**

## Error Handling

### Error Categories

1. **配置错误**
   - 缺少必需的元数据字段
   - 无效的版本号格式
   - 错误的服务器 URL 配置

2. **模型定义错误**
   - Pydantic 模型缺少字段描述
   - 缺少示例值
   - 验证规则不完整

3. **路由定义错误**
   - 缺少响应模型
   - 缺少状态码定义
   - 缺少端点描述

4. **导出错误**
   - 文件写入失败
   - JSON/YAML 序列化错误
   - 权限不足

### Error Handling Strategy

```python
class OpenAPIConfigError(Exception):
    """OpenAPI 配置错误"""
    pass

class SchemaValidationError(Exception):
    """Schema 验证错误"""
    pass

class ExportError(Exception):
    """导出错误"""
    pass

# 错误处理示例
try:
    exporter = OpenAPIExporter(app)
    exporter.export_json("openapi.json")
except PermissionError as e:
    logger.error(f"无法写入文件: {e}")
    raise ExportError(f"文件写入失败: {e}")
except Exception as e:
    logger.error(f"导出失败: {e}")
    raise ExportError(f"未知错误: {e}")
```

### Validation Strategy

1. **启动时验证**: 应用启动时验证 OpenAPI 配置的完整性
2. **运行时验证**: 定期验证生成的 OpenAPI 文档是否符合标准
3. **导出时验证**: 导出前验证文档的有效性
4. **测试时验证**: 在测试中验证所有端点都有完整的文档

## Testing Strategy

### Dual Testing Approach

本项目将采用**单元测试**和**基于属性的测试**相结合的方式：

- **单元测试**: 验证特定示例、边缘情况和错误条件
- **基于属性的测试**: 验证通用属性在所有输入下都成立

两者互补，共同提供全面的测试覆盖。

### Property-Based Testing

**测试库**: 使用 Python 的 `hypothesis` 库进行基于属性的测试

**配置要求**:
- 每个属性测试至少运行 100 次迭代
- 每个测试必须引用设计文档中的属性
- 标签格式: `# Feature: openapi-specification, Property N: [property_text]`

**测试策略**:

1. **生成器设计**
   - 创建智能的 FastAPI 应用生成器
   - 生成各种路由配置组合
   - 生成各种 Pydantic 模型组合

2. **属性验证**
   - 使用 `openapi-spec-validator` 验证生成的文档
   - 验证文档结构的完整性
   - 验证导出功能的正确性

3. **示例测试**
   ```python
   from hypothesis import given, strategies as st
   import hypothesis
   
   @given(st.text(min_size=1), st.text(min_size=1))
   def test_openapi_metadata_completeness(title: str, version: str):
       """
       Feature: openapi-specification, Property 3: 文档元数据完整性
       
       对于任何 title 和 version，生成的 OpenAPI 文档应该包含完整的元数据
       """
       app = create_test_app(title=title, version=version)
       schema = app.openapi()
       
       assert "info" in schema
       assert schema["info"]["title"] == title
       assert schema["info"]["version"] == version
       assert "description" in schema["info"]
       assert "contact" in schema["info"]
       assert "license" in schema["info"]
   ```

### Unit Testing

**测试范围**:

1. **配置测试**
   - 测试 OpenAPIConfig 的各个方法
   - 测试元数据生成
   - 测试服务器列表生成
   - 测试标签元数据生成

2. **Schema 增强测试**
   - 测试 Pydantic 模型的 Field 定义
   - 测试示例值的生成
   - 测试验证规则

3. **路由定义测试**
   - 测试特定端点的文档完整性
   - 测试响应模型的定义
   - 测试错误响应的定义

4. **导出功能测试**
   - 测试 JSON 导出
   - 测试 YAML 导出
   - 测试文件写入
   - 测试错误处理

5. **集成测试**
   - 测试 /openapi.json 端点
   - 测试 /docs 端点（Swagger UI）
   - 测试 /redoc 端点（ReDoc）
   - 测试完整的 API 工作流

### Test Organization

```
tests/
├── unit/
│   ├── test_openapi_config.py
│   ├── test_schemas.py
│   ├── test_routes.py
│   └── test_export.py
├── property/
│   ├── test_openapi_compliance.py
│   ├── test_endpoint_completeness.py
│   ├── test_model_completeness.py
│   └── test_export_validity.py
└── integration/
    ├── test_api_endpoints.py
    └── test_documentation_ui.py
```

### Testing Tools

- **pytest**: 测试框架
- **hypothesis**: 基于属性的测试库
- **httpx**: HTTP 客户端（用于 API 测试）
- **openapi-spec-validator**: OpenAPI 规范验证器
- **pyyaml**: YAML 解析和生成
- **pytest-cov**: 代码覆盖率

### Coverage Goals

- 单元测试覆盖率: ≥ 90%
- 属性测试覆盖所有定义的正确性属性
- 集成测试覆盖所有主要 API 端点

## Implementation Notes

### FastAPI 原生支持

FastAPI 已经内置了 OpenAPI 支持，我们的实现将：
1. **增强**现有的自动生成功能
2. **补充**缺失的元数据和示例
3. **标准化**错误响应格式
4. **优化**文档的可读性和可用性

### 最小化代码变更

设计遵循以下原则：
1. 尽可能使用 FastAPI 的声明式 API
2. 通过装饰器和配置而非代码重写来增强
3. 保持向后兼容性
4. 使用 Pydantic 的原生功能

### 渐进式实现

实现将分阶段进行：
1. **阶段 1**: 增强现有的 Schema 模型
2. **阶段 2**: 改进路由定义和响应模型
3. **阶段 3**: 添加 OpenAPI 配置和自定义
4. **阶段 4**: 实现导出功能
5. **阶段 5**: 完善文档和示例

### 性能考虑

- OpenAPI schema 生成在应用启动时进行一次，然后缓存
- 导出功能按需调用，不影响运行时性能
- 文档 UI（Swagger/ReDoc）使用 CDN 资源，不增加服务器负担

## Dependencies

### Required Libraries

```python
# 已有依赖
fastapi>=0.115.12
pydantic>=2.11.5
uvicorn>=0.34.3

# 新增依赖
pyyaml>=6.0.2              # YAML 导出
openapi-spec-validator>=0.7.1  # OpenAPI 验证
hypothesis>=6.98.0         # 基于属性的测试
```

### Optional Tools

- **Postman**: API 测试和文档导入
- **Insomnia**: API 测试和文档导入
- **openapi-generator**: 客户端 SDK 生成
- **swagger-codegen**: 代码生成工具

## Migration Path

### 从现有实现迁移

1. **保持兼容性**: 现有的 API 端点和行为不变
2. **渐进增强**: 逐步添加 OpenAPI 元数据
3. **测试验证**: 每个阶段都进行充分测试
4. **文档更新**: 同步更新使用文档

### 版本策略

- 当前版本: v1.0.0 (现有实现)
- 目标版本: v3.0.0 (完整 OpenAPI 支持)
- 中间版本: v2.x (渐进式增强)

## Future Enhancements

1. **GraphQL 支持**: 添加 GraphQL schema 导出
2. **API 版本比较**: 自动生成版本差异报告
3. **自动化测试生成**: 从 OpenAPI 规范生成测试用例
4. **性能基准**: 基于 OpenAPI 规范的性能测试
5. **安全扫描**: 基于 OpenAPI 规范的安全漏洞扫描
