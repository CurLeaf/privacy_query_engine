"""
QueryDriver - 核心控制器
职责: 接收原始SQL，协调分析和重写，返回隐私保护后的结果
"""
from typing import Any, Dict

from ..analyzer import SQLAnalyzer, AnalysisResult
from ..policy import PolicyEngine
from ..executor import QueryExecutor
from .context import QueryContext


class QueryDriver:
    """查询驱动器 - 系统核心控制器"""
    
    def __init__(
        self,
        analyzer: SQLAnalyzer = None,
        policy_engine: PolicyEngine = None,
        executor: QueryExecutor = None,
    ):
        self.analyzer = analyzer or SQLAnalyzer()
        self.policy_engine = policy_engine or PolicyEngine()
        self.executor = executor or QueryExecutor()
    
    def process_query(self, original_sql: str, context: QueryContext = None) -> Dict[str, Any]:
        """
        处理查询的主入口
        
        Args:
            original_sql: 原始SQL查询语句
            context: 查询上下文(可选)
            
        Returns:
            包含隐私保护结果的字典
        """
        context = context or QueryContext()
        
        # Step 1: SQL Analysis - 分析SQL语义
        analysis_result = self.analyzer.analyze(original_sql)
        
        # Step 2: Policy Decision - 根据策略决定处理方式
        policy_decision = self.policy_engine.evaluate(analysis_result)
        
        # Step 3: Execute & Apply Privacy Protection - 执行并应用隐私保护
        protected_result = self.executor.execute(
            original_sql=original_sql,
            analysis_result=analysis_result,
            policy_decision=policy_decision,
            context=context,
        )
        
        return protected_result

