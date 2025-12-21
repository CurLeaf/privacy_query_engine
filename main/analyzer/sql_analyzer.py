"""
SQLAnalyzer - SQL分析器
职责: 解析SQL，提取关键信息（如SELECT字段、聚合函数、表名）
"""
from typing import Optional, List
import re

from .models import AnalysisResult, JoinInfo, SubqueryInfo, CTEInfo, WindowFunction


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
            result.joins = self._extract_joins(normalized_sql)
            result.subqueries = self._extract_subqueries(normalized_sql)
            result.ctes = self._extract_ctes(sql)  # 使用原始SQL保留格式
            result.window_functions = self._extract_window_functions(normalized_sql)
            
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
        """提取FROM子句和JOIN子句中的表名"""
        tables = []
        
        # 提取FROM子句中的表名
        from_pattern = r'\bFROM\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?'
        from_matches = re.findall(from_pattern, sql, re.IGNORECASE)
        for match in from_matches:
            table_name = match[0]
            if table_name not in tables:
                tables.append(table_name)
        
        # 提取JOIN子句中的表名
        join_pattern = r'\b(?:INNER\s+JOIN|LEFT\s+(?:OUTER\s+)?JOIN|RIGHT\s+(?:OUTER\s+)?JOIN|FULL\s+(?:OUTER\s+)?JOIN|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?'
        join_matches = re.findall(join_pattern, sql, re.IGNORECASE)
        for match in join_matches:
            table_name = match[0]
            if table_name not in tables:
                tables.append(table_name)
        
        return tables
    
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
    
    def _extract_joins(self, sql: str) -> List[JoinInfo]:
        """提取JOIN操作信息"""
        joins = []
        
        # 简化的JOIN模式，更可靠
        join_pattern = r'\b(INNER\s+JOIN|LEFT\s+(?:OUTER\s+)?JOIN|RIGHT\s+(?:OUTER\s+)?JOIN|FULL\s+(?:OUTER\s+)?JOIN|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?\s+ON\s+(.*?)(?=\s+(?:INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|JOIN|WHERE|GROUP\s+BY|ORDER\s+BY|LIMIT|$)|$)'
        
        matches = re.finditer(join_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            join_type_raw = match.group(1).strip().upper()
            table_name = match.group(2).strip()
            table_alias = match.group(3).strip() if match.group(3) else None
            join_condition = match.group(4).strip()
            
            # 标准化JOIN类型
            if "LEFT" in join_type_raw:
                join_type = "LEFT"
            elif "RIGHT" in join_type_raw:
                join_type = "RIGHT"
            elif "FULL" in join_type_raw:
                join_type = "FULL"
            elif "INNER" in join_type_raw or join_type_raw == "JOIN":
                join_type = "INNER"
            else:
                join_type = "INNER"  # 默认
            
            # 获取所有涉及的表名
            involved_tables = self._extract_tables_from_join(sql, table_name, table_alias)
            
            # 解析JOIN条件
            conditions = self._parse_join_conditions(join_condition)
            
            join_info = JoinInfo(
                join_type=join_type,
                tables=involved_tables,
                join_conditions=conditions,
                estimated_cardinality=1  # 简化实现，默认为1
            )
            
            joins.append(join_info)
        
        return joins
    
    def _extract_tables_from_join(self, sql: str, join_table: str, join_alias: Optional[str] = None) -> List[str]:
        """从JOIN操作中提取所有涉及的表名"""
        tables = []
        
        # 获取主表（FROM子句中的表）
        main_tables = self._extract_tables(sql)
        tables.extend(main_tables)
        
        # 添加JOIN的表
        if join_table not in tables:
            tables.append(join_table)
        
        return tables
    
    def _parse_join_conditions(self, condition_str: str) -> List[str]:
        """解析JOIN条件"""
        if not condition_str:
            return []
        
        # 简化实现：按AND分割条件
        conditions = []
        # 移除多余空白并按AND分割
        condition_str = " ".join(condition_str.split())
        
        # 按AND分割（忽略大小写）
        parts = re.split(r'\s+AND\s+', condition_str, flags=re.IGNORECASE)
        
        for part in parts:
            part = part.strip()
            if part:
                conditions.append(part)
        
        return conditions
    
    def analyze_joins(self, sql: str) -> List[JoinInfo]:
        """分析SQL中的JOIN操作（公共接口方法）"""
        normalized_sql = self._normalize_sql(sql)
        return self._extract_joins(normalized_sql)
    
    def _extract_subqueries(self, sql: str) -> List[SubqueryInfo]:
        """提取子查询信息"""
        subqueries = []
        
        # 查找所有括号内的SELECT语句
        # 使用简化的方法：查找 (SELECT ... ) 模式
        subquery_pattern = r'\(\s*(SELECT\s+.*?)\)'
        
        # 需要递归处理嵌套子查询
        matches = list(re.finditer(subquery_pattern, sql, re.IGNORECASE | re.DOTALL))
        
        for match in matches:
            subquery_sql = match.group(1).strip()
            start_pos = match.start()
            
            # 确定子查询位置和类型
            location, subquery_type = self._determine_subquery_context(sql, start_pos)
            
            # 检查是否为关联子查询
            is_correlated, correlation_columns = self._check_correlation(sql, subquery_sql)
            
            # 提取子查询中的表
            subquery_tables = self._extract_tables(subquery_sql)
            
            subquery_info = SubqueryInfo(
                subquery_type=subquery_type,
                sql=subquery_sql,
                location=location,
                tables=subquery_tables,
                is_correlated=is_correlated,
                correlation_columns=correlation_columns
            )
            
            subqueries.append(subquery_info)
        
        return subqueries
    
    def _determine_subquery_context(self, sql: str, start_pos: int) -> tuple:
        """确定子查询的上下文位置和类型"""
        # 获取子查询前面的SQL片段
        prefix = sql[:start_pos].upper().strip()
        
        # 检查EXISTS
        if prefix.endswith('EXISTS'):
            return 'WHERE', 'EXISTS'
        
        # 检查NOT EXISTS
        if prefix.endswith('NOT EXISTS'):
            return 'WHERE', 'EXISTS'
        
        # 检查IN
        if prefix.endswith('IN'):
            return 'WHERE', 'IN'
        
        # 检查NOT IN
        if prefix.endswith('NOT IN'):
            return 'WHERE', 'IN'
        
        # 检查比较运算符 (标量子查询)
        if re.search(r'[=<>!]+\s*$', prefix):
            return 'WHERE', 'SCALAR'
        
        # 检查FROM子句
        if 'FROM' in prefix and 'WHERE' not in prefix:
            # 检查是否在FROM之后
            from_pos = prefix.rfind('FROM')
            where_pos = prefix.rfind('WHERE')
            if from_pos > where_pos:
                return 'FROM', 'FROM'
        
        # 检查SELECT子句
        select_pos = prefix.rfind('SELECT')
        from_pos = prefix.rfind('FROM')
        if select_pos > from_pos or from_pos == -1:
            return 'SELECT', 'SCALAR'
        
        # 检查HAVING子句
        if 'HAVING' in prefix:
            having_pos = prefix.rfind('HAVING')
            if having_pos > prefix.rfind('WHERE'):
                return 'HAVING', 'SCALAR'
        
        # 默认为WHERE子句中的子查询
        return 'WHERE', 'SCALAR'
    
    def _check_correlation(self, outer_sql: str, subquery_sql: str) -> tuple:
        """检查子查询是否为关联子查询"""
        # 提取外部查询的表别名
        outer_aliases = self._extract_table_aliases(outer_sql)
        
        # 检查子查询中是否引用了外部表的列
        correlation_columns = []
        
        for alias in outer_aliases:
            # 查找子查询中对外部表别名的引用
            pattern = rf'\b{re.escape(alias)}\.\w+'
            matches = re.findall(pattern, subquery_sql, re.IGNORECASE)
            correlation_columns.extend(matches)
        
        is_correlated = len(correlation_columns) > 0
        return is_correlated, list(set(correlation_columns))
    
    def _extract_table_aliases(self, sql: str) -> List[str]:
        """提取SQL中的表别名"""
        aliases = []
        
        # FROM table alias 或 FROM table AS alias
        from_pattern = r'\bFROM\s+(\w+)\s+(?:AS\s+)?(\w+)'
        matches = re.findall(from_pattern, sql, re.IGNORECASE)
        for match in matches:
            if match[1] and match[1].upper() not in ('WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'FULL', 'ON', 'GROUP', 'ORDER', 'HAVING'):
                aliases.append(match[1])
        
        # JOIN table alias
        join_pattern = r'\bJOIN\s+(\w+)\s+(?:AS\s+)?(\w+)'
        matches = re.findall(join_pattern, sql, re.IGNORECASE)
        for match in matches:
            if match[1] and match[1].upper() not in ('ON', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'FULL', 'GROUP', 'ORDER', 'HAVING'):
                aliases.append(match[1])
        
        return aliases
    
    def _extract_ctes(self, sql: str) -> List[CTEInfo]:
        """提取CTE (Common Table Expression) 信息"""
        ctes = []
        
        # 标准化SQL
        normalized_sql = " ".join(sql.split())
        
        # 检查是否以WITH开头
        with_match = re.match(r'\bWITH\s+(RECURSIVE\s+)?', normalized_sql, re.IGNORECASE)
        if not with_match:
            return ctes
        
        is_recursive_global = with_match.group(1) is not None
        start_pos = with_match.end()
        
        # 找到主SELECT（不在括号内的SELECT）
        paren_depth = 0
        i = start_pos
        cte_section = None
        
        while i < len(normalized_sql):
            char = normalized_sql[i]
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif paren_depth == 0:
                # 检查是否是主SELECT
                remaining = normalized_sql[i:].upper()
                if remaining.startswith('SELECT'):
                    cte_section = normalized_sql[start_pos:i].strip()
                    break
            i += 1
        
        if not cte_section:
            return ctes
        
        # 解析各个CTE定义
        cte_parts = self._split_cte_definitions(cte_section)
        
        for cte_part in cte_parts:
            cte_info = self._parse_single_cte(cte_part.strip(), is_recursive_global)
            if cte_info:
                ctes.append(cte_info)
        
        return ctes
    
    def _split_cte_definitions(self, cte_str: str) -> List[str]:
        """分割多个CTE定义"""
        parts = []
        current_part = ""
        paren_depth = 0
        
        i = 0
        while i < len(cte_str):
            char = cte_str[i]
            
            if char == '(':
                paren_depth += 1
                current_part += char
            elif char == ')':
                paren_depth -= 1
                current_part += char
                
                # 检查是否是CTE定义的结束
                if paren_depth == 0:
                    # 查找下一个逗号或结束
                    remaining = cte_str[i+1:].strip()
                    if remaining.startswith(','):
                        parts.append(current_part.strip())
                        current_part = ""
                        i += 1  # 跳过逗号
                        while i < len(cte_str) and cte_str[i] in ' \t\n,':
                            i += 1
                        continue
            else:
                current_part += char
            
            i += 1
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts if parts else [cte_str]
    
    def _parse_single_cte(self, cte_str: str, is_recursive_global: bool) -> Optional[CTEInfo]:
        """解析单个CTE定义"""
        # 格式: name [(col1, col2, ...)] AS (SELECT ...)
        # 更宽松的匹配模式
        cte_pattern = r'^(\w+)\s*(?:\(([^)]+)\))?\s*AS\s*\((.*)\)\s*$'
        match = re.match(cte_pattern, cte_str.strip(), re.IGNORECASE | re.DOTALL)
        
        if not match:
            # 尝试更宽松的匹配 - 不要求结尾的括号
            simple_pattern = r'^(\w+)\s+AS\s*\((.*)\)\s*$'
            match = re.match(simple_pattern, cte_str.strip(), re.IGNORECASE | re.DOTALL)
            if not match:
                return None
            
            name = match.group(1)
            columns = []
            cte_sql = match.group(2).strip()
        else:
            name = match.group(1)
            columns_str = match.group(2)
            columns = [c.strip() for c in columns_str.split(',')] if columns_str else []
            cte_sql = match.group(3).strip()
        
        # 检查是否为递归CTE
        is_recursive = is_recursive_global and self._is_recursive_cte(name, cte_sql)
        
        # 提取CTE引用的表和其他CTE
        references = self._extract_tables(cte_sql)
        
        return CTEInfo(
            name=name,
            sql=cte_sql,
            columns=columns,
            is_recursive=is_recursive,
            references=references
        )
    
    def _is_recursive_cte(self, cte_name: str, cte_sql: str) -> bool:
        """检查CTE是否为递归CTE"""
        # 递归CTE在其定义中引用自身
        pattern = rf'\b{re.escape(cte_name)}\b'
        return bool(re.search(pattern, cte_sql, re.IGNORECASE))
    
    def extract_subqueries(self, sql: str) -> List[SubqueryInfo]:
        """提取子查询（公共接口方法）"""
        normalized_sql = self._normalize_sql(sql)
        return self._extract_subqueries(normalized_sql)
    
    def extract_ctes(self, sql: str) -> List[CTEInfo]:
        """提取CTE（公共接口方法）"""
        return self._extract_ctes(sql)
    
    # 窗口函数相关的函数名
    WINDOW_FUNCTIONS = {
        "ROW_NUMBER", "RANK", "DENSE_RANK", "NTILE",
        "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE", "NTH_VALUE",
        "SUM", "AVG", "COUNT", "MIN", "MAX",
        "PERCENT_RANK", "CUME_DIST"
    }
    
    def _extract_window_functions(self, sql: str) -> List[WindowFunction]:
        """提取窗口函数信息"""
        window_functions = []
        
        # 窗口函数模式: FUNC(...) OVER (...)
        # 需要处理 PARTITION BY 和 ORDER BY
        window_pattern = r'(\w+)\s*\(([^)]*)\)\s+OVER\s*\(([^)]*)\)(?:\s+(?:AS\s+)?(\w+))?'
        
        matches = re.finditer(window_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            func_name = match.group(1).upper()
            func_args = match.group(2).strip() if match.group(2) else ""
            over_clause = match.group(3).strip() if match.group(3) else ""
            alias = match.group(4) if match.group(4) else None
            
            # 检查是否是窗口函数
            if func_name not in self.WINDOW_FUNCTIONS:
                continue
            
            # 解析OVER子句
            partition_by, order_by, window_frame = self._parse_over_clause(over_clause)
            
            # 解析函数参数
            arguments = [arg.strip() for arg in func_args.split(',') if arg.strip()] if func_args else []
            
            window_func = WindowFunction(
                function_name=func_name,
                partition_by=partition_by,
                order_by=order_by,
                window_frame=window_frame,
                alias=alias,
                arguments=arguments
            )
            
            window_functions.append(window_func)
        
        return window_functions
    
    def _parse_over_clause(self, over_clause: str) -> tuple:
        """解析OVER子句"""
        partition_by = []
        order_by = []
        window_frame = None
        
        if not over_clause:
            return partition_by, order_by, window_frame
        
        # 提取PARTITION BY
        partition_pattern = r'PARTITION\s+BY\s+(.*?)(?=ORDER\s+BY|ROWS|RANGE|GROUPS|$)'
        partition_match = re.search(partition_pattern, over_clause, re.IGNORECASE | re.DOTALL)
        if partition_match:
            partition_str = partition_match.group(1).strip()
            partition_by = [col.strip() for col in partition_str.split(',') if col.strip()]
        
        # 提取ORDER BY
        order_pattern = r'ORDER\s+BY\s+(.*?)(?=ROWS|RANGE|GROUPS|$)'
        order_match = re.search(order_pattern, over_clause, re.IGNORECASE | re.DOTALL)
        if order_match:
            order_str = order_match.group(1).strip()
            order_by = [col.strip() for col in order_str.split(',') if col.strip()]
        
        # 提取窗口框架 (ROWS/RANGE/GROUPS BETWEEN...)
        frame_pattern = r'((?:ROWS|RANGE|GROUPS)\s+.*?)$'
        frame_match = re.search(frame_pattern, over_clause, re.IGNORECASE | re.DOTALL)
        if frame_match:
            window_frame = frame_match.group(1).strip()
        
        return partition_by, order_by, window_frame
    
    def analyze_window_functions(self, sql: str) -> List[WindowFunction]:
        """分析窗口函数（公共接口方法）"""
        normalized_sql = self._normalize_sql(sql)
        return self._extract_window_functions(normalized_sql)

