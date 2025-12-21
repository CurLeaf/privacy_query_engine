"""
AnalysisResult - SQL分析结果数据结构
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JoinInfo:
    """JOIN操作信息"""
    join_type: str  # INNER, LEFT, RIGHT, FULL
    tables: List[str]
    join_conditions: List[str]
    estimated_cardinality: int = 1


@dataclass
class SubqueryInfo:
    """子查询信息"""
    subquery_type: str  # SCALAR, EXISTS, IN, FROM, CORRELATED
    sql: str  # 子查询SQL
    location: str  # WHERE, SELECT, FROM, HAVING
    tables: List[str] = field(default_factory=list)
    is_correlated: bool = False
    correlation_columns: List[str] = field(default_factory=list)


@dataclass
class CTEInfo:
    """CTE (Common Table Expression) 信息"""
    name: str  # CTE名称
    sql: str  # CTE定义的SQL
    columns: List[str] = field(default_factory=list)
    is_recursive: bool = False
    references: List[str] = field(default_factory=list)  # 引用的其他CTE或表


@dataclass
class WindowFunction:
    """窗口函数信息"""
    function_name: str  # 函数名 (ROW_NUMBER, RANK, SUM, etc.)
    partition_by: List[str] = field(default_factory=list)  # PARTITION BY 列
    order_by: List[str] = field(default_factory=list)  # ORDER BY 列
    window_frame: Optional[str] = None  # 窗口框架 (ROWS/RANGE BETWEEN...)
    alias: Optional[str] = None  # 别名
    arguments: List[str] = field(default_factory=list)  # 函数参数


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
    
    # JOIN操作信息
    joins: List[JoinInfo] = field(default_factory=list)
    
    # 子查询信息
    subqueries: List[SubqueryInfo] = field(default_factory=list)
    
    # CTE信息
    ctes: List[CTEInfo] = field(default_factory=list)
    
    # 窗口函数信息
    window_functions: List[WindowFunction] = field(default_factory=list)
    
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

