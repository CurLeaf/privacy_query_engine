"""
Privacy-Utility Evaluation Module - 隐私-可用性评估模块

提供脱敏效果的量化评估能力：
- 隐私保护程度评估
- 数据可用性评估
- 综合报告生成
"""
from .privacy_metrics import (
    PrivacyMetrics,
    KAnonymityChecker,
    LDiversityChecker,
    ReidentificationRiskAnalyzer,
)
from .utility_metrics import (
    UtilityMetrics,
    StatisticalSimilarity,
    QueryAccuracy,
    InformationLoss,
)
from .evaluator import (
    PrivacyUtilityEvaluator,
    EvaluationReport,
    EvaluationConfig,
)

__all__ = [
    # 隐私指标
    "PrivacyMetrics",
    "KAnonymityChecker",
    "LDiversityChecker",
    "ReidentificationRiskAnalyzer",
    # 可用性指标
    "UtilityMetrics",
    "StatisticalSimilarity",
    "QueryAccuracy",
    "InformationLoss",
    # 综合评估
    "PrivacyUtilityEvaluator",
    "EvaluationReport",
    "EvaluationConfig",
]
