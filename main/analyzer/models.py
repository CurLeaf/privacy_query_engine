"""
AnalysisResult - SQL分析结果数据结构
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AnalysisResult:
    """SQL分析结果"""
    
    # 涉及的表名
    tables: List[str] = field(default_factory=list)
    
    # SELECT子句中的列名
    select_columns: List[str] = field(default_factory=list)
    
    # 聚合函数列表 (e.g., ["COUNT", "SUM", "AVG"])
    aggregations: List[str] = field(default_factory=list)
    
    # 是否包含WHERE子句
    has_where: bool = False
    
    # WHERE子句条件(简化表示)
    where_conditions: List[str] = field(default_factory=list)
    
    # 是否为聚合查询
    is_aggregate_query: bool = False
    
    # GROUP BY字段
    group_by_columns: List[str] = field(default_factory=list)
    
    # 原始SQL
    original_sql: str = ""
    
    # 解析是否成功
    is_valid: bool = True
    
    # 错误信息
    error_message: Optional[str] = None
    
    # 扩展元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_aggregation(self, *funcs: str) -> bool:
        """检查是否包含指定的聚合函数"""
        upper_funcs = {f.upper() for f in funcs}
        return any(agg.upper() in upper_funcs for agg in self.aggregations)
    
    def has_sensitive_columns(self, sensitive_list: List[str]) -> bool:
        """检查是否包含敏感列"""
        lower_sensitive = {s.lower() for s in sensitive_list}
        return any(col.lower() in lower_sensitive for col in self.select_columns)

