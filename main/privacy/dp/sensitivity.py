"""
SensitivityAnalyzer - 敏感度分析器
职责: 分析查询的敏感度
"""
from typing import Dict, Any


class SensitivityAnalyzer:
    """查询敏感度分析器"""
    
    # 常见聚合函数的默认敏感度
    DEFAULT_SENSITIVITIES = {
        "COUNT": 1.0,      # COUNT的敏感度为1
        "SUM": None,       # SUM需要知道数据范围
        "AVG": None,       # AVG需要知道数据范围和记录数
        "MIN": None,       # MIN/MAX通常敏感度较高
        "MAX": None,
    }
    
    def __init__(self, bounds: Dict[str, tuple] = None):
        """
        初始化敏感度分析器
        
        Args:
            bounds: 字段值域范围, e.g., {"age": (0, 150), "salary": (0, 1000000)}
        """
        self.bounds = bounds or {}
    
    def analyze(self, aggregation: str, column: str = None) -> float:
        """
        分析聚合函数的敏感度
        
        Args:
            aggregation: 聚合函数名称 (COUNT, SUM, AVG等)
            column: 聚合的列名 (用于查找值域范围)
            
        Returns:
            敏感度值
        """
        agg_upper = aggregation.upper()
        
        # COUNT的敏感度固定为1
        if agg_upper == "COUNT":
            return 1.0
        
        # 对于SUM, 敏感度 = max_value - min_value (单条记录的最大影响)
        if agg_upper == "SUM" and column and column in self.bounds:
            lower, upper = self.bounds[column]
            return upper - lower
        
        # 默认敏感度 (保守估计)
        return self.DEFAULT_SENSITIVITIES.get(agg_upper) or 1.0
    
    def set_bounds(self, column: str, lower: float, upper: float):
        """设置列的值域范围"""
        self.bounds[column] = (lower, upper)

