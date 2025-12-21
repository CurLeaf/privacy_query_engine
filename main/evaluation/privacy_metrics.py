"""
Privacy Metrics - 隐私保护程度评估指标

评估脱敏后数据的隐私保护效果。
"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import math


@dataclass
class PrivacyMetrics:
    """隐私指标汇总"""
    k_anonymity: int = 0                    # K-匿名性级别
    l_diversity: int = 0                    # L-多样性级别
    t_closeness: float = 0.0                # T-接近度
    reidentification_risk: float = 0.0      # 重识别风险 (0-1)
    uniqueness_ratio: float = 0.0           # 唯一记录比例
    suppression_ratio: float = 0.0          # 抑制比例
    entropy: float = 0.0                    # 敏感属性熵
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def privacy_score(self) -> float:
        """综合隐私得分 (0-100)"""
        score = 100.0
        
        # K-匿名性贡献 (k>=5 满分)
        k_score = min(self.k_anonymity / 5.0, 1.0) * 30
        
        # 重识别风险贡献 (风险越低越好)
        risk_score = (1 - self.reidentification_risk) * 40
        
        # 唯一性贡献 (唯一记录越少越好)
        unique_score = (1 - self.uniqueness_ratio) * 20
        
        # L-多样性贡献
        l_score = min(self.l_diversity / 3.0, 1.0) * 10
        
        return k_score + risk_score + unique_score + l_score


class KAnonymityChecker:
    """K-匿名性检查器"""
    
    def check(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> int:
        """
        检查数据的 K-匿名性级别
        
        Args:
            data: 数据列表
            quasi_identifiers: 准标识符列表
            
        Returns:
            K 值（最小等价类大小）
        """
        if not data or not quasi_identifiers:
            return 0
        
        # 计算等价类
        equivalence_classes = self._compute_equivalence_classes(data, quasi_identifiers)
        
        if not equivalence_classes:
            return 0
        
        # 返回最小等价类大小
        return min(len(rows) for rows in equivalence_classes.values())
    
    def get_equivalence_class_distribution(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> Dict[int, int]:
        """
        获取等价类大小分布
        
        Returns:
            {等价类大小: 数量}
        """
        equivalence_classes = self._compute_equivalence_classes(data, quasi_identifiers)
        
        size_distribution = Counter(len(rows) for rows in equivalence_classes.values())
        return dict(sorted(size_distribution.items()))
    
    def _compute_equivalence_classes(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> Dict[tuple, List[int]]:
        """计算等价类"""
        classes = {}
        for i, row in enumerate(data):
            key = tuple(row.get(qi) for qi in quasi_identifiers)
            if key not in classes:
                classes[key] = []
            classes[key].append(i)
        return classes


class LDiversityChecker:
    """L-多样性检查器"""
    
    def check(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        sensitive_attribute: str,
    ) -> int:
        """
        检查数据的 L-多样性级别
        
        Args:
            data: 数据列表
            quasi_identifiers: 准标识符列表
            sensitive_attribute: 敏感属性
            
        Returns:
            L 值（每个等价类中敏感属性的最小不同值数量）
        """
        if not data or not quasi_identifiers or not sensitive_attribute:
            return 0
        
        # 计算等价类
        classes = {}
        for i, row in enumerate(data):
            key = tuple(row.get(qi) for qi in quasi_identifiers)
            if key not in classes:
                classes[key] = []
            classes[key].append(i)
        
        if not classes:
            return 0
        
        # 计算每个等价类的敏感属性多样性
        min_diversity = float('inf')
        for key, row_indices in classes.items():
            sensitive_values = set()
            for idx in row_indices:
                val = data[idx].get(sensitive_attribute)
                if val is not None:
                    sensitive_values.add(val)
            
            diversity = len(sensitive_values)
            min_diversity = min(min_diversity, diversity)
        
        return int(min_diversity) if min_diversity != float('inf') else 0
    
    def check_entropy_l_diversity(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
        sensitive_attribute: str,
        l: int,
    ) -> bool:
        """
        检查熵 L-多样性
        
        每个等价类的敏感属性熵 >= log(l)
        """
        classes = self._compute_equivalence_classes(data, quasi_identifiers)
        threshold = math.log(l) if l > 0 else 0
        
        for key, row_indices in classes.items():
            # 计算敏感属性分布
            value_counts = Counter(
                data[idx].get(sensitive_attribute) for idx in row_indices
            )
            
            # 计算熵
            total = sum(value_counts.values())
            entropy = 0.0
            for count in value_counts.values():
                if count > 0:
                    p = count / total
                    entropy -= p * math.log(p)
            
            if entropy < threshold:
                return False
        
        return True
    
    def _compute_equivalence_classes(self, data, quasi_identifiers):
        classes = {}
        for i, row in enumerate(data):
            key = tuple(row.get(qi) for qi in quasi_identifiers)
            if key not in classes:
                classes[key] = []
            classes[key].append(i)
        return classes


class ReidentificationRiskAnalyzer:
    """重识别风险分析器"""
    
    def analyze(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> Dict[str, float]:
        """
        分析重识别风险
        
        Args:
            data: 数据列表
            quasi_identifiers: 准标识符列表
            
        Returns:
            风险指标字典
        """
        if not data:
            return {"overall_risk": 0.0, "max_risk": 0.0, "avg_risk": 0.0}
        
        # 计算等价类
        classes = {}
        for i, row in enumerate(data):
            key = tuple(row.get(qi) for qi in quasi_identifiers)
            if key not in classes:
                classes[key] = []
            classes[key].append(i)
        
        # 计算每条记录的重识别风险 (1/等价类大小)
        risks = []
        for key, row_indices in classes.items():
            risk = 1.0 / len(row_indices)
            risks.extend([risk] * len(row_indices))
        
        # 唯一记录数
        unique_count = sum(1 for rows in classes.values() if len(rows) == 1)
        
        return {
            "overall_risk": sum(risks) / len(risks) if risks else 0.0,
            "max_risk": max(risks) if risks else 0.0,
            "avg_risk": sum(risks) / len(risks) if risks else 0.0,
            "unique_records": unique_count,
            "uniqueness_ratio": unique_count / len(data) if data else 0.0,
            "equivalence_class_count": len(classes),
        }
    
    def prosecutor_risk(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> float:
        """
        检察官风险 - 攻击者知道目标在数据集中
        
        风险 = max(1/|EC|) 对所有等价类 EC
        """
        classes = self._compute_equivalence_classes(data, quasi_identifiers)
        if not classes:
            return 0.0
        
        return max(1.0 / len(rows) for rows in classes.values())
    
    def journalist_risk(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> float:
        """
        记者风险 - 攻击者不确定目标是否在数据集中
        
        风险 = 唯一记录数 / 总记录数
        """
        classes = self._compute_equivalence_classes(data, quasi_identifiers)
        if not classes or not data:
            return 0.0
        
        unique_count = sum(1 for rows in classes.values() if len(rows) == 1)
        return unique_count / len(data)
    
    def marketer_risk(
        self,
        data: List[Dict[str, Any]],
        quasi_identifiers: List[str],
    ) -> float:
        """
        营销者风险 - 平均重识别风险
        
        风险 = avg(1/|EC|) 对所有记录
        """
        result = self.analyze(data, quasi_identifiers)
        return result["avg_risk"]
    
    def _compute_equivalence_classes(self, data, quasi_identifiers):
        classes = {}
        for i, row in enumerate(data):
            key = tuple(row.get(qi) for qi in quasi_identifiers)
            if key not in classes:
                classes[key] = []
            classes[key].append(i)
        return classes
