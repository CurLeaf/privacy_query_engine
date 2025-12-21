"""
Utility Metrics - 数据可用性评估指标

评估脱敏后数据的可用性和分析价值。
"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import math


@dataclass
class UtilityMetrics:
    """可用性指标汇总"""
    information_loss: float = 0.0           # 信息损失率 (0-1)
    statistical_similarity: float = 0.0     # 统计相似度 (0-1)
    query_accuracy: float = 0.0             # 查询准确度 (0-1)
    completeness: float = 0.0               # 数据完整性 (0-1)
    granularity_loss: float = 0.0           # 粒度损失 (0-1)
    record_linkage_quality: float = 0.0     # 记录链接质量 (0-1)
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def utility_score(self) -> float:
        """综合可用性得分 (0-100)"""
        # 信息损失贡献 (损失越低越好)
        info_score = (1 - self.information_loss) * 30
        
        # 统计相似度贡献
        stat_score = self.statistical_similarity * 30
        
        # 查询准确度贡献
        query_score = self.query_accuracy * 25
        
        # 完整性贡献
        complete_score = self.completeness * 15
        
        return info_score + stat_score + query_score + complete_score


class InformationLoss:
    """信息损失计算器"""
    
    def calculate(
        self,
        original: List[Dict[str, Any]],
        protected: List[Dict[str, Any]],
        columns: List[str] = None,
    ) -> Dict[str, float]:
        """
        计算信息损失
        
        Args:
            original: 原始数据
            protected: 脱敏后数据
            columns: 要比较的列（None 表示所有列）
            
        Returns:
            信息损失指标
        """
        if not original or not protected:
            return {"overall": 0.0, "by_column": {}}
        
        if len(original) != len(protected):
            return {"overall": 1.0, "by_column": {}, "error": "Row count mismatch"}
        
        if columns is None:
            columns = list(original[0].keys())
        
        column_losses = {}
        total_cells = 0
        changed_cells = 0
        suppressed_cells = 0
        
        for col in columns:
            col_changed = 0
            col_suppressed = 0
            col_total = 0
            
            for orig_row, prot_row in zip(original, protected):
                orig_val = orig_row.get(col)
                prot_val = prot_row.get(col)
                col_total += 1
                
                if orig_val != prot_val:
                    col_changed += 1
                    if prot_val == "*SUPPRESSED*":
                        col_suppressed += 1
            
            column_losses[col] = {
                "change_ratio": col_changed / col_total if col_total > 0 else 0,
                "suppression_ratio": col_suppressed / col_total if col_total > 0 else 0,
            }
            
            total_cells += col_total
            changed_cells += col_changed
            suppressed_cells += col_suppressed
        
        return {
            "overall": changed_cells / total_cells if total_cells > 0 else 0,
            "suppression_ratio": suppressed_cells / total_cells if total_cells > 0 else 0,
            "by_column": column_losses,
        }
    
    def calculate_generalization_loss(
        self,
        original: List[Dict[str, Any]],
        protected: List[Dict[str, Any]],
        column: str,
        hierarchy_depth: int = 5,
    ) -> float:
        """
        计算泛化导致的信息损失
        
        基于泛化层级深度计算
        """
        if not original or not protected:
            return 0.0
        
        total_loss = 0.0
        count = 0
        
        for orig_row, prot_row in zip(original, protected):
            orig_val = str(orig_row.get(column, ""))
            prot_val = str(prot_row.get(column, ""))
            
            if orig_val == prot_val:
                loss = 0.0
            elif prot_val == "*SUPPRESSED*":
                loss = 1.0
            elif "-" in prot_val:  # 范围泛化 (如 "20-29")
                loss = 0.5
            else:
                # 基于字符串相似度估算
                loss = 1 - self._string_similarity(orig_val, prot_val)
            
            total_loss += loss
            count += 1
        
        return total_loss / count if count > 0 else 0.0
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """简单的字符串相似度"""
        if s1 == s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        # 使用公共前缀长度
        common = 0
        for c1, c2 in zip(s1, s2):
            if c1 == c2:
                common += 1
            else:
                break
        
        return common / max(len(s1), len(s2))


class StatisticalSimilarity:
    """统计相似度计算器"""
    
    def calculate(
        self,
        original: List[Dict[str, Any]],
        protected: List[Dict[str, Any]],
        numeric_columns: List[str] = None,
        categorical_columns: List[str] = None,
    ) -> Dict[str, float]:
        """
        计算统计相似度
        
        Args:
            original: 原始数据
            protected: 脱敏后数据
            numeric_columns: 数值列
            categorical_columns: 分类列
            
        Returns:
            统计相似度指标
        """
        if not original or not protected:
            return {"overall": 0.0}
        
        similarities = []
        details = {}
        
        # 数值列统计相似度
        if numeric_columns:
            for col in numeric_columns:
                sim = self._numeric_similarity(original, protected, col)
                similarities.append(sim)
                details[f"{col}_numeric"] = sim
        
        # 分类列分布相似度
        if categorical_columns:
            for col in categorical_columns:
                sim = self._categorical_similarity(original, protected, col)
                similarities.append(sim)
                details[f"{col}_categorical"] = sim
        
        overall = sum(similarities) / len(similarities) if similarities else 0.0
        
        return {
            "overall": overall,
            "details": details,
        }
    
    def _numeric_similarity(
        self,
        original: List[Dict],
        protected: List[Dict],
        column: str,
    ) -> float:
        """数值列统计相似度"""
        orig_values = self._extract_numeric(original, column)
        prot_values = self._extract_numeric(protected, column)
        
        if not orig_values or not prot_values:
            return 0.0
        
        # 比较均值
        orig_mean = sum(orig_values) / len(orig_values)
        prot_mean = sum(prot_values) / len(prot_values)
        mean_sim = 1 - abs(orig_mean - prot_mean) / (abs(orig_mean) + 1e-10)
        mean_sim = max(0, min(1, mean_sim))
        
        # 比较标准差
        orig_std = self._std(orig_values)
        prot_std = self._std(prot_values)
        std_sim = 1 - abs(orig_std - prot_std) / (orig_std + 1e-10)
        std_sim = max(0, min(1, std_sim))
        
        return (mean_sim + std_sim) / 2
    
    def _categorical_similarity(
        self,
        original: List[Dict],
        protected: List[Dict],
        column: str,
    ) -> float:
        """分类列分布相似度 (使用 Jensen-Shannon 散度)"""
        orig_dist = self._get_distribution(original, column)
        prot_dist = self._get_distribution(protected, column)
        
        if not orig_dist or not prot_dist:
            return 0.0
        
        # 获取所有类别
        all_categories = set(orig_dist.keys()) | set(prot_dist.keys())
        
        # 计算 JS 散度
        js_div = self._js_divergence(orig_dist, prot_dist, all_categories)
        
        # 转换为相似度 (0-1)
        return 1 - min(js_div, 1.0)
    
    def _extract_numeric(self, data: List[Dict], column: str) -> List[float]:
        """提取数值"""
        values = []
        for row in data:
            val = row.get(column)
            if val is not None:
                try:
                    # 处理范围值 (如 "20-29")
                    if isinstance(val, str) and "-" in val:
                        parts = val.split("-")
                        val = (float(parts[0]) + float(parts[1])) / 2
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        return values
    
    def _get_distribution(self, data: List[Dict], column: str) -> Dict[str, float]:
        """获取分布"""
        counts = Counter(row.get(column) for row in data)
        total = sum(counts.values())
        return {k: v / total for k, v in counts.items()} if total > 0 else {}
    
    def _std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def _js_divergence(
        self,
        p: Dict[str, float],
        q: Dict[str, float],
        categories: set,
    ) -> float:
        """Jensen-Shannon 散度"""
        # 计算中间分布
        m = {}
        for cat in categories:
            m[cat] = (p.get(cat, 0) + q.get(cat, 0)) / 2
        
        # 计算 KL 散度
        kl_pm = self._kl_divergence(p, m, categories)
        kl_qm = self._kl_divergence(q, m, categories)
        
        return (kl_pm + kl_qm) / 2
    
    def _kl_divergence(
        self,
        p: Dict[str, float],
        q: Dict[str, float],
        categories: set,
    ) -> float:
        """KL 散度"""
        kl = 0.0
        for cat in categories:
            p_val = p.get(cat, 0)
            q_val = q.get(cat, 1e-10)  # 避免除零
            if p_val > 0:
                kl += p_val * math.log(p_val / q_val)
        return kl


class QueryAccuracy:
    """查询准确度评估器"""
    
    def evaluate(
        self,
        original: List[Dict[str, Any]],
        protected: List[Dict[str, Any]],
        queries: List[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        评估查询准确度
        
        Args:
            original: 原始数据
            protected: 脱敏后数据
            queries: 测试查询列表
            
        Returns:
            查询准确度指标
        """
        if queries is None:
            queries = self._generate_default_queries(original)
        
        if not queries:
            return {"overall": 1.0, "details": []}
        
        accuracies = []
        details = []
        
        for query in queries:
            query_type = query.get("type", "count")
            column = query.get("column")
            
            if query_type == "count":
                orig_result = len(original)
                prot_result = len(protected)
            elif query_type == "sum" and column:
                orig_result = self._sum_column(original, column)
                prot_result = self._sum_column(protected, column)
            elif query_type == "avg" and column:
                orig_result = self._avg_column(original, column)
                prot_result = self._avg_column(protected, column)
            elif query_type == "distinct" and column:
                orig_result = len(set(row.get(column) for row in original))
                prot_result = len(set(row.get(column) for row in protected))
            else:
                continue
            
            # 计算相对误差
            if orig_result != 0:
                accuracy = 1 - abs(orig_result - prot_result) / abs(orig_result)
            else:
                accuracy = 1.0 if prot_result == 0 else 0.0
            
            accuracy = max(0, min(1, accuracy))
            accuracies.append(accuracy)
            
            details.append({
                "query": query,
                "original_result": orig_result,
                "protected_result": prot_result,
                "accuracy": accuracy,
            })
        
        return {
            "overall": sum(accuracies) / len(accuracies) if accuracies else 1.0,
            "details": details,
        }
    
    def _generate_default_queries(self, data: List[Dict]) -> List[Dict]:
        """生成默认测试查询"""
        if not data:
            return []
        
        queries = [{"type": "count"}]
        
        # 为每个数值列生成聚合查询
        for col in data[0].keys():
            sample_val = data[0].get(col)
            if isinstance(sample_val, (int, float)):
                queries.append({"type": "sum", "column": col})
                queries.append({"type": "avg", "column": col})
            queries.append({"type": "distinct", "column": col})
        
        return queries
    
    def _sum_column(self, data: List[Dict], column: str) -> float:
        """求和"""
        total = 0.0
        for row in data:
            val = row.get(column)
            if val is not None:
                try:
                    if isinstance(val, str) and "-" in val:
                        parts = val.split("-")
                        val = (float(parts[0]) + float(parts[1])) / 2
                    total += float(val)
                except (ValueError, TypeError):
                    pass
        return total
    
    def _avg_column(self, data: List[Dict], column: str) -> float:
        """平均值"""
        values = []
        for row in data:
            val = row.get(column)
            if val is not None:
                try:
                    if isinstance(val, str) and "-" in val:
                        parts = val.split("-")
                        val = (float(parts[0]) + float(parts[1])) / 2
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        return sum(values) / len(values) if values else 0.0
