"""
SQLAnalyzer - SQL分析器
职责: 解析SQL，提取关键信息（如SELECT字段、聚合函数、表名）
"""
from typing import Optional
import re

from .models import AnalysisResult


class SQLAnalyzer:
    """SQL语义分析器"""
    
    # 支持的聚合函数
    AGGREGATE_FUNCTIONS = {"COUNT", "SUM", "AVG", "MIN", "MAX"}
    
    def analyze(self, sql: str) -> AnalysisResult:
        """
        分析SQL语句，提取关键信息
        
        Args:
            sql: 原始SQL语句
            
        Returns:
            AnalysisResult对象
        """
        result = AnalysisResult(original_sql=sql)
        
        try:
            # 标准化SQL
            normalized_sql = self._normalize_sql(sql)
            
            # 提取各部分信息
            result.tables = self._extract_tables(normalized_sql)
            result.select_columns = self._extract_select_columns(normalized_sql)
            result.aggregations = self._extract_aggregations(normalized_sql)
            result.has_where = self._has_where_clause(normalized_sql)
            result.where_conditions = self._extract_where_conditions(normalized_sql)
            result.group_by_columns = self._extract_group_by(normalized_sql)
            
            # 判断是否为聚合查询
            result.is_aggregate_query = len(result.aggregations) > 0
            
        except Exception as e:
            result.is_valid = False
            result.error_message = str(e)
        
        return result
    
    def _normalize_sql(self, sql: str) -> str:
        """标准化SQL语句"""
        # 移除多余空白
        sql = " ".join(sql.split())
        return sql.strip()
    
    def _extract_tables(self, sql: str) -> list:
        """提取FROM子句中的表名"""
        # 简单实现: 匹配 FROM table_name
        pattern = r'\bFROM\s+(\w+)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        return matches
    
    def _extract_select_columns(self, sql: str) -> list:
        """提取SELECT子句中的列名"""
        # 匹配SELECT和FROM之间的内容
        pattern = r'\bSELECT\s+(.*?)\s+FROM\b'
        match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return []
        
        columns_str = match.group(1)
        
        # 分割列名(简单处理,不考虑复杂表达式)
        columns = []
        for col in columns_str.split(","):
            col = col.strip()
            # 提取别名或原始列名
            if " AS " in col.upper():
                col = col.split()[-1]  # 取别名
            # 移除聚合函数包装
            if "(" in col:
                # 对于聚合函数,保留整体
                columns.append(col)
            else:
                columns.append(col)
        
        return columns
    
    def _extract_aggregations(self, sql: str) -> list:
        """提取聚合函数"""
        aggregations = []
        upper_sql = sql.upper()
        
        for func in self.AGGREGATE_FUNCTIONS:
            pattern = rf'\b{func}\s*\('
            if re.search(pattern, upper_sql):
                aggregations.append(func)
        
        return aggregations
    
    def _has_where_clause(self, sql: str) -> bool:
        """检查是否包含WHERE子句"""
        return bool(re.search(r'\bWHERE\b', sql, re.IGNORECASE))
    
    def _extract_where_conditions(self, sql: str) -> list:
        """提取WHERE子句条件(简化实现)"""
        pattern = r'\bWHERE\s+(.*?)(?:\bGROUP BY\b|\bORDER BY\b|\bLIMIT\b|$)'
        match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return []
        
        conditions_str = match.group(1).strip()
        # 简单返回整个条件字符串
        return [conditions_str] if conditions_str else []
    
    def _extract_group_by(self, sql: str) -> list:
        """提取GROUP BY字段"""
        pattern = r'\bGROUP BY\s+(.*?)(?:\bHAVING\b|\bORDER BY\b|\bLIMIT\b|$)'
        match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return []
        
        group_str = match.group(1).strip()
        return [col.strip() for col in group_str.split(",")]

