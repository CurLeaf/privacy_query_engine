# Implementation Plan: OpenAPI Specification

## Overview

本实现计划将 OpenAPI 规范功能分解为离散的编码步骤。每个任务都建立在前面的任务之上，最终实现完整的标准 OpenAPI 文档生成、增强和导出功能。实现将充分利用 FastAPI 的原生 OpenAPI 支持，通过声明式配置和增强来达到目标。

## Tasks

- [ ] 1. 设置项目依赖和配置
  - 在 requirements.txt 中添加新的依赖项（pyyaml, openapi-spec-validator, hypothesis）
  - 创建测试配置文件
  - 设置测试目录结构
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 2. 创建 OpenAPI 配置模块
  - [ ] 2.1 实现 OpenAPIConfig 类
    - 创建 `main/api/openapi_config.py` 文件
    - 实现 `get_metadata()` 方法返回 API 元数据
    - 实现 `get_servers()` 方法返回服务器列表
    - 实现 `get_tags_metadata()` 方法返回标签描述
    - _Requirements: 1.5, 8.2_

  - [ ]* 2.2 编写 OpenAPIConfig 单元测试
    - 测试元数据生成的完整性
    - 测试服务器列表格式
    - 测试标签元数据格式
    - _Requirements: 1.5, 8.2_

- [ ] 3. 增强 Pydantic Schema 模型
  - [ ] 3.1 重构现有 schemas.py
    - 为所有字段添加详细的 Field 描述
    - 为每个模型添加多个示例（使用 model_config）
    - 添加验证规则和约束
    - 确保所有字段都有类型注解
    - _Requirements: 3.2, 3.3, 3.5_

  - [ ] 3.2 创建标准化的 ErrorResponse 模型
    - 添加 error_code 字段
    - 添加 timestamp 字段
    - 提供多个错误场景的示例
    - _Requirements: 4.1, 4.3, 4.5_

  - [ ] 3.3 创建预算相关的响应模型
    - 创建 BudgetStatusResponse 模型
    - 创建 BudgetHistoryResponse 模型
    - 添加完整的字段描述和示例
    - _Requirements: 2.4, 3.2_

  - [ ] 3.4 创建审计和性能相关的响应模型
    - 创建 AuditLogResponse 模型
    - 创建 PerformanceMetricResponse 模型
    - 添加完整的字段描述和示例
    - _Requirements: 2.4, 3.2_

  - [ ]* 3.5 编写 Schema 模型的单元测试
    - 测试字段验证规则
    - 测试示例值的有效性
    - 测试模型序列化
    - _Requirements: 3.2, 3.3_

- [ ] 4. Checkpoint - 验证模型定义
  - 确保所有测试通过，询问用户是否有问题

- [ ] 5. 增强 API 路由定义
  - [ ] 5.1 增强 /protect-query 端点
    - 添加详细的 description（包括使用示例）
    - 为所有状态码添加 responses 定义
    - 为每个响应添加多个示例
    - 添加适当的标签
    - _Requirements: 2.1, 2.2, 2.5_

  - [ ] 5.2 增强预算管理端点
    - 为 /budget/{user_id} 添加完整文档
    - 为 /budget/{user_id}/reset 添加完整文档
    - 为 /budget/{user_id}/history 添加完整文档
    - 添加请求参数说明和响应示例
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 5.3 增强审计日志端点
    - 为所有 /audit/* 端点添加完整文档
    - 添加查询参数的详细说明
    - 添加响应示例
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 5.4 增强性能监控端点
    - 为所有 /performance/* 端点添加完整文档
    - 添加查询参数的详细说明
    - 添加响应示例
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 5.5 标准化所有端点的错误响应
    - 确保所有端点都定义了 400, 500 错误响应
    - 使用统一的 ErrorResponse 模型
    - 为每个错误场景提供示例
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [ ]* 5.6 编写路由定义的集成测试
    - 测试每个端点的文档完整性
    - 验证响应模型的正确性
    - 测试错误响应
    - _Requirements: 2.1, 2.2, 2.4_

- [ ] 6. Checkpoint - 验证路由增强
  - 确保所有测试通过，询问用户是否有问题

- [ ] 7. 自定义 OpenAPI Schema 生成
  - [ ] 7.1 在 server.py 中实现 custom_openapi 函数
    - 集成 OpenAPIConfig 的元数据
    - 添加服务器列表
    - 添加标签元数据
    - 添加联系信息和许可证
    - 添加外部文档链接
    - _Requirements: 1.5, 8.2_

  - [ ] 7.2 添加安全方案定义（可选）
    - 在 components.securitySchemes 中定义 API Key 认证
    - 为需要认证的端点添加 security 声明
    - _Requirements: 6.1, 6.3_

  - [ ] 7.3 将 custom_openapi 函数绑定到 FastAPI 应用
    - 在 create_app() 中设置 app.openapi = custom_openapi
    - 验证 /openapi.json 端点返回自定义的 schema
    - _Requirements: 1.2_

  - [ ]* 7.4 编写 OpenAPI schema 自定义的单元测试
    - 测试元数据的正确性
    - 测试服务器列表
    - 测试标签定义
    - _Requirements: 1.5, 8.2_

- [ ] 8. 实现 OpenAPI 导出功能
  - [ ] 8.1 创建 OpenAPIExporter 类
    - 创建 `main/api/export.py` 文件
    - 实现 `export_json()` 方法
    - 实现 `export_yaml()` 方法
    - 实现 `get_schema()` 方法
    - 添加错误处理
    - _Requirements: 9.1, 9.2_

  - [ ] 8.2 添加导出 CLI 命令（可选）
    - 创建命令行接口用于导出 OpenAPI 规范
    - 支持指定输出路径和格式
    - _Requirements: 9.1, 9.2_

  - [ ]* 8.3 编写导出功能的单元测试
    - 测试 JSON 导出的有效性
    - 测试 YAML 导出的有效性
    - 测试文件写入
    - 测试错误处理
    - _Requirements: 9.1, 9.2_

- [ ] 9. Checkpoint - 验证导出功能
  - 确保所有测试通过，询问用户是否有问题

- [ ] 10. 实现基于属性的测试
  - [ ]* 10.1 编写 OpenAPI 标准合规性属性测试
    - **Property 1: OpenAPI 标准合规性**
    - **Validates: Requirements 1.1**
    - 使用 hypothesis 生成各种配置
    - 使用 openapi-spec-validator 验证生成的文档
    - 运行至少 100 次迭代

  - [ ]* 10.2 编写端点完整性属性测试
    - **Property 2: 端点完整性**
    - **Validates: Requirements 1.3**
    - 验证所有注册的路由都在 OpenAPI 文档中
    - 运行至少 100 次迭代

  - [ ]* 10.3 编写文档元数据完整性属性测试
    - **Property 3: 文档元数据完整性**
    - **Validates: Requirements 1.4, 1.5**
    - 验证 info 部分包含所有必需字段
    - 运行至少 100 次迭代

  - [ ]* 10.4 编写端点文档完整性属性测试
    - **Property 4: 端点文档完整性**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    - 验证每个端点都有完整的文档
    - 运行至少 100 次迭代

  - [ ]* 10.5 编写数据模型完整性属性测试
    - **Property 6: 数据模型完整性**
    - **Validates: Requirements 3.2, 3.3, 3.5**
    - 验证所有模型都有完整的 schema 定义
    - 运行至少 100 次迭代

  - [ ]* 10.6 编写错误响应一致性属性测试
    - **Property 8: 错误响应一致性**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    - 验证所有错误响应使用统一结构
    - 运行至少 100 次迭代

  - [ ]* 10.7 编写导出有效性属性测试
    - **Property 13: JSON 导出有效性**
    - **Property 14: YAML 导出有效性**
    - **Property 15: OpenAPI 工具兼容性**
    - **Validates: Requirements 9.1, 9.2, 9.3**
    - 验证导出的文档可以被标准工具解析
    - 运行至少 100 次迭代

- [ ] 11. 验证交互式文档界面
  - [ ] 11.1 测试 Swagger UI 可访问性
    - 验证 /docs 端点返回 Swagger UI
    - 检查页面加载正常
    - _Requirements: 7.1_

  - [ ] 11.2 测试 ReDoc 可访问性
    - 验证 /redoc 端点返回 ReDoc
    - 检查页面加载正常
    - _Requirements: 7.2_

  - [ ]* 11.3 编写文档界面的集成测试
    - 测试 /docs 端点
    - 测试 /redoc 端点
    - 测试 /openapi.json 端点
    - _Requirements: 7.1, 7.2, 1.2_

- [ ] 12. 完善文档和示例
  - [ ] 12.1 更新 README.md
    - 添加 OpenAPI 功能说明
    - 添加使用示例
    - 添加导出命令说明
    - _Requirements: 10.1, 10.2_

  - [ ] 12.2 创建 API 使用示例文档
    - 创建常见查询场景的示例
    - 创建预算管理工作流示例
    - 创建错误处理示例
    - _Requirements: 10.2, 10.3, 10.4_

  - [ ] 12.3 添加 OpenAPI 集成指南
    - 说明如何导入到 Postman
    - 说明如何导入到 Insomnia
    - 说明如何生成客户端 SDK
    - _Requirements: 9.4, 9.5_

- [ ] 13. Final Checkpoint - 完整性验证
  - 运行所有测试（单元测试 + 属性测试 + 集成测试）
  - 验证代码覆盖率达到 90%
  - 手动测试交互式文档界面
  - 导出 OpenAPI 规范并验证
  - 询问用户是否有问题或需要调整

## Notes

- 标记 `*` 的任务是可选的测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求以确保可追溯性
- Checkpoint 任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证特定示例和边缘情况
