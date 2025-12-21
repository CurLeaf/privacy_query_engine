"""
Privacy Query Engine - 差分隐私与去标识化查询引擎

主要组件:
- core: 核心控制器 (QueryDriver, QueryContext)
- analyzer: SQL分析器 (SQLAnalyzer)
- privacy: 隐私处理 (DP, DeID)
- policy: 策略引擎 (PolicyEngine)
- executor: 查询执行器 (QueryExecutor)
- data: 结构化数据处理 (CSV, DataFrame)
- evaluation: 隐私-可用性评估
- api: HTTP服务 (FastAPI)
"""

__version__ = "2.0.0"

from .core import QueryDriver, QueryContext
from .analyzer import SQLAnalyzer, AnalysisResult
from .policy import PolicyEngine, PolicyDecision, ConfigManager
from .executor import QueryExecutor
from .data import CSVPrivacyProcessor, DataFrameProcessor, SchemaDetector
from .evaluation import PrivacyUtilityEvaluator, EvaluationReport, EvaluationConfig

__all__ = [
    # Core
    "QueryDriver",
    "QueryContext",
    # Analyzer
    "SQLAnalyzer",
    "AnalysisResult",
    # Policy
    "PolicyEngine",
    "PolicyDecision",
    "ConfigManager",
    # Executor
    "QueryExecutor",
    # Data Processing
    "CSVPrivacyProcessor",
    "DataFrameProcessor",
    "SchemaDetector",
    # Evaluation
    "PrivacyUtilityEvaluator",
    "EvaluationReport",
    "EvaluationConfig",
]
