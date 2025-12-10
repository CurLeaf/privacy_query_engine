# Privacy Query Engine - 项目目录结构

> **文档日期**：2025年12月10日  
> **项目名称**：差分隐私与去标识化查询引擎

---

## 📁 完整目录结构

```
privacy_query_engine/
│
├── 📄 README.md                        # 项目说明文档
├── 📄 LICENSE                          # 许可证
├── 📄 SECURITY.md                      # 安全政策
├── 📄 CODE_OF_CONDUCT.md               # 行为准则
├── 📄 CONTRIBUTING.md                  # 贡献指南
├── 📄 Makefile                         # 构建脚本
├── 📄 pyproject.toml                   # Python项目配置
├── 📄 setup.cfg                        # 安装配置
├── 📄 requirements.txt                 # 项目依赖
├── 📄 cookiecutter-config-file.yml     # Cookiecutter配置
│
├── 📂 main/                            # 🎯 主代码目录
│   ├── __init__.py                     # 包入口，导出主要组件
│   ├── __main__.py                     # 命令行入口
│   ├── example.py                      # 示例代码
│   │
│   ├── 📂 core/                        # 核心模块
│   │   ├── __init__.py
│   │   ├── driver.py                   # QueryDriver - 核心控制器
│   │   └── context.py                  # QueryContext - 查询上下文
│   │
│   ├── 📂 analyzer/                    # 能力域1: SQL分析
│   │   ├── __init__.py
│   │   ├── sql_analyzer.py             # SQLAnalyzer - SQL解析器
│   │   └── models.py                   # AnalysisResult - 分析结果模型
│   │
│   ├── 📂 privacy/                     # 能力域2: 隐私处理
│   │   ├── __init__.py
│   │   │
│   │   ├── 📂 dp/                      # 差分隐私子模块
│   │   │   ├── __init__.py
│   │   │   ├── mechanisms.py           # Laplace/Gaussian噪声机制
│   │   │   ├── rewriter.py             # DPRewriter - DP重写器
│   │   │   └── sensitivity.py          # SensitivityAnalyzer - 敏感度分析
│   │   │
│   │   └── 📂 deid/                    # 去标识化子模块
│   │       ├── __init__.py
│   │       ├── methods.py              # 脱敏方法(hash/mask/generalize)
│   │       └── rewriter.py             # DeIDRewriter - 去标识化重写器
│   │
│   ├── 📂 policy/                      # 能力域3: 策略管理
│   │   ├── __init__.py
│   │   ├── engine.py                   # PolicyEngine - 策略引擎
│   │   └── config.py                   # ConfigManager - 配置管理器
│   │
│   ├── 📂 executor/                    # 能力域4: 查询执行
│   │   ├── __init__.py
│   │   ├── query_executor.py           # QueryExecutor - 查询执行器
│   │   ├── database.py                 # DatabaseConnection - 数据库连接
│   │   └── mock.py                     # MockDatabaseExecutor - Mock执行器
│   │
│   ├── 📂 api/                         # 能力域5: API服务
│   │   ├── __init__.py
│   │   ├── server.py                   # FastAPI服务入口
│   │   ├── routes.py                   # HTTP路由定义
│   │   └── schemas.py                  # Pydantic请求/响应模型
│   │
│   └── 📂 utils/                       # 工具模块
│       ├── __init__.py
│       └── exceptions.py               # 自定义异常类
│
├── 📂 config/                          # 配置文件目录
│   └── policy.yaml                     # 策略配置文件
│
├── 📂 tests/                           # 测试目录
│   ├── __init__.py
│   │
│   ├── 📂 test_analyzer/               # SQL分析器测试
│   │   ├── __init__.py
│   │   └── test_sql_analyzer.py
│   │
│   ├── 📂 test_privacy/                # 隐私模块测试
│   │   ├── __init__.py
│   │   ├── test_dp.py                  # 差分隐私测试
│   │   └── test_deid.py                # 去标识化测试
│   │
│   ├── 📂 test_policy/                 # 策略引擎测试
│   │   ├── __init__.py
│   │   └── test_engine.py
│   │
│   ├── 📂 test_executor/               # 执行器测试
│   │   └── __init__.py
│   │
│   ├── 📂 test_api/                    # API测试
│   │   ├── __init__.py
│   │   └── test_routes.py
│   │
│   └── 📂 test_example/                # 示例测试
│       └── test_hello.py
│
├── 📂 doc/                             # 文档目录
│   ├── construct.md                    # 项目结构文档 (本文件)
│   │
│   └── 📂 design/                      # 设计文档
│       ├── README.md
│       ├── 差分隐私与去标识化查询引擎 MVP 设计文档.md
│       ├── 开发路线.md
│       └── 数据处理与差分隐私流程分析.md
│
├── 📂 docker/                          # Docker配置
│   ├── Dockerfile
│   └── README.md
│
└── 📂 assets/                          # 静态资源
    └── 📂 images/
        └── coverage.svg                # 测试覆盖率徽章
```

---

## 🧩 模块职责说明

### 能力域对应关系

| 能力域 | 目录 | 核心组件 | 职责 |
|--------|------|----------|------|
| **核心控制** | `main/core/` | `QueryDriver`, `QueryContext` | 协调整个查询处理流程 |
| **域1: SQL分析** | `main/analyzer/` | `SQLAnalyzer`, `AnalysisResult` | 解析SQL语义，提取关键信息 |
| **域2: 隐私处理** | `main/privacy/` | `DPRewriter`, `DeIDRewriter` | 应用差分隐私或去标识化 |
| **域3: 策略管理** | `main/policy/` | `PolicyEngine`, `ConfigManager` | 根据规则决定处理方式 |
| **域4: 查询执行** | `main/executor/` | `QueryExecutor`, `DatabaseConnection` | 执行SQL并封装结果 |
| **域5: API服务** | `main/api/` | `FastAPI Server`, `Routes` | 提供HTTP接口 |

---

## 📊 数据流向

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   HTTP API  │────▶│ QueryDriver │────▶│ SQLAnalyzer │
│  (api/)     │     │  (core/)    │     │ (analyzer/) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ PolicyEngine  │
                   │  (policy/)    │
                   └───────┬───────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      ┌───────────────┐         ┌───────────────┐
      │  DPRewriter   │         │ DeIDRewriter  │
      │ (privacy/dp/) │         │(privacy/deid/)│
      └───────┬───────┘         └───────┬───────┘
              │                         │
              └────────────┬────────────┘
                           ▼
                   ┌───────────────┐
                   │QueryExecutor  │
                   │ (executor/)   │
                   └───────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ Protected     │
                   │ Result        │
                   └───────────────┘
```

---

## 🔧 关键文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `main/__init__.py` | 包入口，导出 `QueryDriver`, `SQLAnalyzer`, `PolicyEngine` 等 |
| `main/core/driver.py` | 系统核心控制器，协调各模块完成查询处理 |
| `main/privacy/dp/mechanisms.py` | 实现 Laplace/Gaussian 噪声机制 |
| `main/privacy/deid/methods.py` | 实现 hash/mask/generalize 等脱敏方法 |
| `main/api/server.py` | FastAPI 服务入口，启动 HTTP 服务 |
| `config/policy.yaml` | 策略配置文件，定义规则和敏感列 |

### 配置文件

| 文件 | 说明 |
|------|------|
| `pyproject.toml` | Python项目元数据和构建配置 |
| `requirements.txt` | 项目运行依赖 |
| `setup.cfg` | 安装和工具配置 |
| `config/policy.yaml` | 隐私策略规则配置 |

---

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 启动API服务
uvicorn main.api.server:app --reload --port 8000

# 访问API文档
# http://localhost:8000/docs
```

---

## 📝 备注

- 所有模块使用 `__init__.py` 导出公共接口
- 测试目录结构与主代码目录结构一一对应
- `config/policy.yaml` 用于配置策略规则，可热加载
- `mock.py` 提供开发阶段的模拟数据库执行器

---

> **文档状态**: 已完成  
> **最后更新**: 2025-12-10

