"""
Privacy-Utility Evaluator - 综合评估器

整合隐私和可用性指标，生成综合评估报告。
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from .privacy_metrics import (
    PrivacyMetrics,
    KAnonymityChecker,
    LDiversityChecker,
    ReidentificationRiskAnalyzer,
)
from .utility_metrics import (
    UtilityMetrics,
    InformationLoss,
    StatisticalSimilarity,
    QueryAccuracy,
)


@dataclass
class EvaluationConfig:
    """评估配置"""
    # 准标识符列表
    quasi_identifiers: List[str] = field(default_factory=list)
    # 敏感属性
    sensitive_attribute: Optional[str] = None
    # 数值列（用于统计相似度）
    numeric_columns: List[str] = field(default_factory=list)
    # 分类列（用于分布相似度）
    categorical_columns: List[str] = field(default_factory=list)
    # 自定义测试查询
    test_queries: List[Dict[str, Any]] = field(default_factory=list)
    # 目标 K 值
    target_k: int = 5
    # 目标 L 值
    target_l: int = 3


@dataclass
class EvaluationReport:
    """评估报告"""
    # 基本信息
    timestamp: datetime = field(default_factory=datetime.now)
    original_row_count: int = 0
    protected_row_count: int = 0
    
    # 隐私指标
    privacy_metrics: PrivacyMetrics = field(default_factory=PrivacyMetrics)
    
    # 可用性指标
    utility_metrics: UtilityMetrics = field(default_factory=UtilityMetrics)
    
    # 综合评分
    privacy_score: float = 0.0      # 0-100
    utility_score: float = 0.0      # 0-100
    overall_score: float = 0.0      # 0-100
    
    # 合规性检查
    k_anonymity_satisfied: bool = False
    l_diversity_satisfied: bool = False
    
    # 建议
    recommendations: List[str] = field(default_factory=list)
    
    # 详细数据
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "original_row_count": self.original_row_count,
            "protected_row_count": self.protected_row_count,
            "privacy_metrics": {
                "k_anonymity": self.privacy_metrics.k_anonymity,
                "l_diversity": self.privacy_metrics.l_diversity,
                "reidentification_risk": self.privacy_metrics.reidentification_risk,
                "uniqueness_ratio": self.privacy_metrics.uniqueness_ratio,
                "privacy_score": self.privacy_metrics.privacy_score,
            },
            "utility_metrics": {
                "information_loss": self.utility_metrics.information_loss,
                "statistical_similarity": self.utility_metrics.statistical_similarity,
                "query_accuracy": self.utility_metrics.query_accuracy,
                "completeness": self.utility_metrics.completeness,
                "utility_score": self.utility_metrics.utility_score,
            },
            "scores": {
                "privacy_score": self.privacy_score,
                "utility_score": self.utility_score,
                "overall_score": self.overall_score,
            },
            "compliance": {
                "k_anonymity_satisfied": self.k_anonymity_satisfied,
                "l_diversity_satisfied": self.l_diversity_satisfied,
            },
            "recommendations": self.recommendations,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def summary(self) -> str:
        """生成摘要文本"""
        lines = [
            "=" * 60,
            "隐私-可用性评估报告",
            "=" * 60,
            f"评估时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"原始数据行数: {self.original_row_count}",
            f"处理后数据行数: {self.protected_row_count}",
            "",
            "【隐私保护指标】",
            f"  K-匿名性级别: {self.privacy_metrics.k_anonymity}",
            f"  L-多样性级别: {self.privacy_metrics.l_diversity}",
            f"  重识别风险: {self.privacy_metrics.reidentification_risk:.2%}",
            f"  唯一记录比例: {self.privacy_metrics.uniqueness_ratio:.2%}",
            f"  隐私得分: {self.privacy_score:.1f}/100",
            "",
            "【数据可用性指标】",
            f"  信息损失率: {self.utility_metrics.information_loss:.2%}",
            f"  统计相似度: {self.utility_metrics.statistical_similarity:.2%}",
            f"  查询准确度: {self.utility_metrics.query_accuracy:.2%}",
            f"  数据完整性: {self.utility_metrics.completeness:.2%}",
            f"  可用性得分: {self.utility_score:.1f}/100",
            "",
            "【综合评估】",
            f"  综合得分: {self.overall_score:.1f}/100",
            f"  K-匿名性合规: {'✓' if self.k_anonymity_satisfied else '✗'}",
            f"  L-多样性合规: {'✓' if self.l_diversity_satisfied else '✗'}",
            "",
            "【改进建议】",
        ]
        
        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"  {i}. {rec}")
        
        if not self.recommendations:
            lines.append("  无")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


class PrivacyUtilityEvaluator:
    """
    隐私-可用性综合评估器
    
    功能：
    - 评估脱敏后数据的隐私保护程度
    - 评估脱敏后数据的可用性
    - 生成综合评估报告
    - 提供改进建议
    
    使用示例：
        evaluator = PrivacyUtilityEvaluator()
        
        config = EvaluationConfig(
            quasi_identifiers=["age", "zipcode", "gender"],
            sensitive_attribute="disease",
            numeric_columns=["age", "income"],
            target_k=5,
            target_l=3,
        )
        
        report = evaluator.evaluate(original_data, protected_data, config)
        print(report.summary())
    """
    
    def __init__(self):
        self.k_checker = KAnonymityChecker()
        self.l_checker = LDiversityChecker()
        self.risk_analyzer = ReidentificationRiskAnalyzer()
        self.info_loss = InformationLoss()
        self.stat_similarity = StatisticalSimilarity()
        self.query_accuracy = QueryAccuracy()
    
    def evaluate(
        self,
        original: List[Dict[str, Any]],
        protected: List[Dict[str, Any]],
        config: EvaluationConfig = None,
    ) -> EvaluationReport:
        """
        执行综合评估
        
        Args:
            original: 原始数据
            protected: 脱敏后数据
            config: 评估配置
            
        Returns:
            EvaluationReport 评估报告
        """
        config = config or EvaluationConfig()
        report = EvaluationReport(
            original_row_count=len(original),
            protected_row_count=len(protected),
        )
        
        # 评估隐私指标
        report.privacy_metrics = self._evaluate_privacy(protected, config)
        
        # 评估可用性指标
        report.utility_metrics = self._evaluate_utility(original, protected, config)
        
        # 计算综合得分
        report.privacy_score = report.privacy_metrics.privacy_score
        report.utility_score = report.utility_metrics.utility_score
        report.overall_score = self._calculate_overall_score(
            report.privacy_score, report.utility_score
        )
        
        # 合规性检查
        report.k_anonymity_satisfied = report.privacy_metrics.k_anonymity >= config.target_k
        report.l_diversity_satisfied = report.privacy_metrics.l_diversity >= config.target_l
        
        # 生成建议
        report.recommendations = self._generate_recommendations(report, config)
        
        return report
    
    def _evaluate_privacy(
        self,
        protected: List[Dict[str, Any]],
        config: EvaluationConfig,
    ) -> PrivacyMetrics:
        """评估隐私指标"""
        metrics = PrivacyMetrics()
        
        if not config.quasi_identifiers:
            return metrics
        
        # K-匿名性
        metrics.k_anonymity = self.k_checker.check(protected, config.quasi_identifiers)
        
        # L-多样性
        if config.sensitive_attribute:
            metrics.l_diversity = self.l_checker.check(
                protected, config.quasi_identifiers, config.sensitive_attribute
            )
        
        # 重识别风险
        risk_result = self.risk_analyzer.analyze(protected, config.quasi_identifiers)
        metrics.reidentification_risk = risk_result["overall_risk"]
        metrics.uniqueness_ratio = risk_result["uniqueness_ratio"]
        
        # 抑制比例
        suppressed = sum(
            1 for row in protected
            if any(row.get(qi) == "*SUPPRESSED*" for qi in config.quasi_identifiers)
        )
        metrics.suppression_ratio = suppressed / len(protected) if protected else 0
        
        metrics.details = {
            "risk_analysis": risk_result,
            "equivalence_class_distribution": self.k_checker.get_equivalence_class_distribution(
                protected, config.quasi_identifiers
            ),
        }
        
        return metrics
    
    def _evaluate_utility(
        self,
        original: List[Dict[str, Any]],
        protected: List[Dict[str, Any]],
        config: EvaluationConfig,
    ) -> UtilityMetrics:
        """评估可用性指标"""
        metrics = UtilityMetrics()
        
        # 信息损失
        loss_result = self.info_loss.calculate(original, protected)
        metrics.information_loss = loss_result["overall"]
        
        # 统计相似度
        stat_result = self.stat_similarity.calculate(
            original, protected,
            config.numeric_columns,
            config.categorical_columns,
        )
        metrics.statistical_similarity = stat_result["overall"]
        
        # 查询准确度
        query_result = self.query_accuracy.evaluate(
            original, protected, config.test_queries or None
        )
        metrics.query_accuracy = query_result["overall"]
        
        # 完整性（非抑制记录比例）
        suppressed = sum(
            1 for row in protected
            if any(v == "*SUPPRESSED*" for v in row.values())
        )
        metrics.completeness = 1 - (suppressed / len(protected)) if protected else 1.0
        
        metrics.details = {
            "information_loss": loss_result,
            "statistical_similarity": stat_result,
            "query_accuracy": query_result,
        }
        
        return metrics
    
    def _calculate_overall_score(
        self,
        privacy_score: float,
        utility_score: float,
        privacy_weight: float = 0.5,
    ) -> float:
        """
        计算综合得分
        
        使用调和平均数，确保两个指标都不能太低
        """
        if privacy_score <= 0 or utility_score <= 0:
            return 0.0
        
        # 调和平均
        harmonic_mean = 2 * privacy_score * utility_score / (privacy_score + utility_score)
        
        return harmonic_mean
    
    def _generate_recommendations(
        self,
        report: EvaluationReport,
        config: EvaluationConfig,
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 隐私相关建议
        if report.privacy_metrics.k_anonymity < config.target_k:
            recommendations.append(
                f"K-匿名性不足 (当前: {report.privacy_metrics.k_anonymity}, "
                f"目标: {config.target_k})。建议增加泛化程度或抑制更多稀有记录。"
            )
        
        if report.privacy_metrics.reidentification_risk > 0.1:
            recommendations.append(
                f"重识别风险较高 ({report.privacy_metrics.reidentification_risk:.1%})。"
                "建议增加准标识符的泛化程度。"
            )
        
        if report.privacy_metrics.uniqueness_ratio > 0.05:
            recommendations.append(
                f"唯一记录比例过高 ({report.privacy_metrics.uniqueness_ratio:.1%})。"
                "建议对准标识符进行更多泛化或抑制唯一记录。"
            )
        
        # 可用性相关建议
        if report.utility_metrics.information_loss > 0.3:
            recommendations.append(
                f"信息损失较大 ({report.utility_metrics.information_loss:.1%})。"
                "建议使用更精细的泛化策略或减少脱敏列数。"
            )
        
        if report.utility_metrics.statistical_similarity < 0.8:
            recommendations.append(
                f"统计相似度较低 ({report.utility_metrics.statistical_similarity:.1%})。"
                "脱敏后数据的统计特性与原始数据差异较大，可能影响分析结果。"
            )
        
        if report.utility_metrics.query_accuracy < 0.9:
            recommendations.append(
                f"查询准确度不足 ({report.utility_metrics.query_accuracy:.1%})。"
                "聚合查询结果与原始数据有较大偏差。"
            )
        
        # 平衡建议
        if report.privacy_score > 80 and report.utility_score < 60:
            recommendations.append(
                "隐私保护较强但可用性较低。如果业务允许，可以适当降低保护强度以提高可用性。"
            )
        
        if report.utility_score > 80 and report.privacy_score < 60:
            recommendations.append(
                "数据可用性较高但隐私保护不足。建议加强脱敏措施以满足合规要求。"
            )
        
        if not recommendations:
            recommendations.append("数据脱敏效果良好，隐私保护和可用性达到较好平衡。")
        
        return recommendations
    
    def quick_evaluate(
        self,
        original: List[Dict[str, Any]],
        protected: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> Dict[str, Any]:
        """
        快速评估（简化版）
        
        Args:
            original: 原始数据
            protected: 脱敏后数据
            quasi_identifiers: 准标识符列表
            
        Returns:
            简化的评估结果
        """
        config = EvaluationConfig(quasi_identifiers=quasi_identifiers)
        report = self.evaluate(original, protected, config)
        
        return {
            "k_anonymity": report.privacy_metrics.k_anonymity,
            "reidentification_risk": report.privacy_metrics.reidentification_risk,
            "information_loss": report.utility_metrics.information_loss,
            "privacy_score": report.privacy_score,
            "utility_score": report.utility_score,
            "overall_score": report.overall_score,
        }
