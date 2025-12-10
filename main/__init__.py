"""
Privacy Query Engine - 差分隐私与去标识化查询引擎

主要组件:
- core: 核心控制器 (QueryDriver, QueryContext)
- analyzer: SQL分析器 (SQLAnalyzer)
- privacy: 隐私处理 (DP, DeID)
- policy: 策略引擎 (PolicyEngine)
- executor: 查询执行器 (QueryExecutor)
- api: HTTP服务 (FastAPI)
"""

__version__ = "1.0.0"

from .core import QueryDriver, QueryContext
from .analyzer import SQLAnalyzer, AnalysisResult
from .policy import PolicyEngine, PolicyDecision, ConfigManager
from .executor import QueryExecutor

__all__ = [
    "QueryDriver",
    "QueryContext",
    "SQLAnalyzer",
    "AnalysisResult",
    "PolicyEngine",
    "PolicyDecision",
    "ConfigManager",
    "QueryExecutor",
]
