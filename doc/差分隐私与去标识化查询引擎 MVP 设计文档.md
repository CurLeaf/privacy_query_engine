# 差分隐私与去标识化查询引擎 MVP 设计文档

> **当前日期**: Thursday, December 04, 2025
>
> **目标**: 构建一个能够拦截用户SQL查询，并根据策略自动应用差分隐私（DP）或去标识化（DeID）处理的最小系统。

## 核心业务逻辑 (MVP Focus)

系统的灵魂在于 `Query Driver` 模块。它必须能：

1.  **接收原始SQL查询**。
2.  **分析SQL语义** (`SQL Analysis`)。
3.  **根据上下文和策略，决定应用 DP 或 DeID**。
4.  **调用对应的算法模块** (`Differential Privacy` 或 `DeIdentification`)。
5.  **生成并返回经过隐私保护处理的新SQL**。

**MVP 的核心假设**：
- 我们暂不考虑复杂的预算管理、噪声后处理、元数据提取等高级功能。
- 假设所有查询都走同一个路径，由 `Query Driver` 统一处理。
- 策略是硬编码或从简单配置文件读取。

---

## MVP 版本 1: 最小可运行核心 (v1.0)

### 目标
实现一个命令行工具或简单的HTTP服务，输入一条SQL，输出经过DP或DeID处理后的SQL。

### 核心组件

#### 1. `QueryDriver` (核心控制器)
- **职责**: 接收原始SQL，协调分析和重写。
- **输入**: `original_sql: str`
- **输出**: `protected_sql: str`
- **伪代码**:
    ```python
    def process_query(original_sql):
        # Step 1: SQL Analysis
        analysis_result = sql_analyzer.analyze(original_sql)
        
        # Step 2: Decide Policy (MVP: Hardcoded for now)
        if should_apply_dp(analysis_result): # e.g., contains COUNT/SUM/AVG
            protected_sql = dp_rewriter.rewrite(original_sql, analysis_result)
        else:
            protected_sql = deid_rewriter.rewrite(original_sql, analysis_result)
            
        return protected_sql
    ```

#### 2. `SQLAnalyzer` (SQL分析器)
- **职责**: 解析SQL，提取关键信息（如SELECT字段、聚合函数、表名）。
- **技术选型**: 使用开源SQL解析库，如 `sqlparse` (Python) 或 `JSqlParser` (Java)。
- **输出**: 一个包含分析结果的对象，例如 `{ "aggregations": ["COUNT", "SUM"], "tables": ["users"] }`。

#### 3. `DP Rewriter` (差分隐私重写器)
- **职责**: 对聚合查询添加噪声。
- **MVP实现**: 仅支持最简单的 `COUNT(*)` 查询。
    - 输入: `SELECT COUNT(*) FROM users WHERE age > 30;`
    - 输出: `SELECT COUNT(*) + LAPLACE_NOISE(epsilon=1.0) FROM users WHERE age > 30;`
    - **注意**: 这里只是示意，实际需要调用 `DP Alg` 模块计算噪声值。

#### 4. `DeID Rewriter` (去标识化重写器)
- **职责**: 对非聚合查询，对敏感列进行脱敏。
- **MVP实现**: 仅支持对 `name` 列进行哈希或掩码。
    - 输入: `SELECT name, email FROM users;`
    - 输出: `SELECT SHA256(name) as name, MASK(email) as email FROM users;`

---

## MVP 版本 2: 引入基础策略与配置 (v2.0)

### 目标
让系统不再依赖硬编码，而是通过配置文件或API来定义处理策略。

### 新增组件

#### 1. `PolicyEngine` (策略引擎)
- **职责**: 根据分析结果和预设规则，决定使用DP还是DeID。
- **输入**: `analysis_result`, `policy_config`
- **输出**: `action: "DP" | "DeID"`
- **配置示例** (`policy.yaml`):
    ```yaml
    rules:
      - condition: "aggregations contains 'COUNT' or 'SUM'"
        action: "DP"
        parameters:
          epsilon: 1.0
      - condition: "select_columns contains 'name' or 'email'"
        action: "DeID"
        parameters:
          method: "HASH"
    ```

#### 2. `ConfigManager` (配置管理器)
- **职责**: 加载并管理 `policy.yaml` 配置文件。

---

## MVP 版本 3: 添加基本的API接口 (v3.0)

### 目标
将核心功能暴露为HTTP服务，便于集成。

### 新增组件

#### 1. `HttpService` (HTTP服务)
- **端点**: `POST /api/v1/protect-query`
- **请求体**:
    ```json
    {
      "sql": "SELECT COUNT(*) FROM users;"
    }
    ```
- **响应体**:
    ```json
    {
      "status": "success",
      "protected_sql": "SELECT COUNT(*) + LAPLACE_NOISE(epsilon=1.0) FROM users;"
    }
    ```

---

## 后续演进路线图

在MVP稳定后，可以按以下顺序逐步完善系统：

### 阶段 1: 完善核心处理能力

- **DP Handling**:
    - 实现完整的 `DP Alg` 模块，支持多种差分隐私机制（如Gaussian, Laplace）。
    - 实现 `Noise` 模块，精确计算和注入噪声。
    - 实现 `Sensitivity` 分析，自动计算查询的敏感度。
    - 实现 `DP post-processing`，对结果进行平滑或校正。
- **DeID Handling**:
    - 实现 `DeID analysis`，识别更多敏感字段类型。
    - 实现 `DeID rewriter`，支持多种脱敏方法（掩码、泛化、假名化）。
    - 实现 `DeID Post-processing`，确保脱敏后数据的一致性。

### 阶段 2: 引入预算与审计

- **Privacy Budget Management**:
    - 实现 `Privacy Accountant`，记录每个用户的隐私预算消耗。
    - 实现 `CRUD API`，用于管理和查询预算。
    - 在 `Query Driver` 中集成预算检查，在预算不足时拒绝查询或返回错误。
- **Reporting**:
    - 记录每次查询的处理日志，包括使用的策略、消耗的预算、处理时间等。

### 阶段 3: 元数据与扩展性

- **Metadata Management**:
    - 实现 `Extract metadata` 功能，从数据库中自动获取表结构、字段类型等信息。
    - 将元数据存储在 `RDS` 或其他数据库中，供 `SQL Analysis` 和 `Policy Engine` 使用。
- **Query Context**:
    - 扩展 `Query Context`，包含用户身份、查询来源、时间戳等，用于更精细化的策略控制。

### 阶段 4: 生产级特性

- **性能优化**: 缓存分析结果、异步处理、批量查询。
- **高可用**: 集群部署、负载均衡。
- **安全**: 认证授权、审计追踪、数据加密。
- **监控告警**: 集成Prometheus/Grafana，监控系统健康状态和预算使用情况。

---

## 总结

这个MVP设计从最核心的“查询重写”功能出发，通过三个迭代版本，快速验证了系统的核心价值。后续的完善工作都是围绕这个核心展开，确保每一步都建立在坚实的基础上，避免过早陷入复杂细节。这符合敏捷开发的原则，也确保了项目能够快速交付价值。

希望这份文档能为您提供清晰的开发路线！