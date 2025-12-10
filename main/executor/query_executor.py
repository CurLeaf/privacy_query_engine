"""
QueryExecutor - 查询执行器
职责: 协调查询执行和隐私保护处理
"""
from typing import Any, Dict, Optional

from ..analyzer import AnalysisResult
from ..policy import PolicyDecision
from ..privacy import DPRewriter, DeIDRewriter
from ..core.context import QueryContext
from .mock import MockDatabaseExecutor
from .database import DatabaseConnection


class QueryExecutor:
    """查询执行器"""
    
    def __init__(
        self,
        db_connection: DatabaseConnection = None,
        use_mock: bool = True,
    ):
        """
        初始化查询执行器
        
        Args:
            db_connection: 数据库连接 (可选)
            use_mock: 是否使用Mock执行器 (开发模式)
        """
        self.db_connection = db_connection
        self.use_mock = use_mock
        self.mock_executor = MockDatabaseExecutor() if use_mock else None
        
        # 隐私处理器
        self.dp_rewriter = DPRewriter()
        self.deid_rewriter = DeIDRewriter()
    
    def execute(
        self,
        original_sql: str,
        analysis_result: AnalysisResult,
        policy_decision: PolicyDecision,
        context: QueryContext = None,
    ) -> Dict[str, Any]:
        """
        执行查询并应用隐私保护
        
        Args:
            original_sql: 原始SQL
            analysis_result: SQL分析结果
            policy_decision: 策略决策
            context: 查询上下文
            
        Returns:
            统一响应格式的结果
        """
        # Step 1: 执行原始查询获取结果
        raw_result = self._execute_sql(original_sql)
        
        # Step 2: 根据策略应用隐私保护
        if policy_decision.action == "DP":
            return self._apply_dp_protection(
                original_sql, raw_result, policy_decision
            )
        elif policy_decision.action == "DeID":
            return self._apply_deid_protection(
                original_sql, raw_result, policy_decision, analysis_result
            )
        elif policy_decision.action == "REJECT":
            return self._create_error_response(
                original_sql, policy_decision.reason
            )
        else:
            # PASS: 不需要隐私保护
            return self._create_pass_response(original_sql, raw_result)
    
    def _execute_sql(self, sql: str) -> Any:
        """执行SQL查询"""
        if self.use_mock and self.mock_executor:
            return self.mock_executor.execute(sql)
        elif self.db_connection:
            # 检查是否是聚合查询
            sql_upper = sql.upper()
            if any(agg in sql_upper for agg in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]):
                return self.db_connection.execute_scalar(sql)
            return self.db_connection.execute_query(sql)
        else:
            raise RuntimeError("No database connection available")
    
    def _apply_dp_protection(
        self,
        original_sql: str,
        raw_result: Any,
        policy_decision: PolicyDecision
    ) -> Dict[str, Any]:
        """应用差分隐私保护"""
        params = policy_decision.params
        epsilon = params.get("epsilon", 1.0)
        mechanism = params.get("mechanism", "laplace")
        sensitivity = params.get("sensitivity", 1.0)
        
        # 添加噪声
        protected_result = self.dp_rewriter.apply_dp(
            raw_result, epsilon, sensitivity, mechanism
        )
        
        # 构建响应
        return {
            "type": "DP",
            "original_query": original_sql,
            "protected_result": protected_result,
            "privacy_info": {
                "epsilon": epsilon,
                "method": mechanism.capitalize(),
                "sensitivity": sensitivity,
            }
        }
    
    def _apply_deid_protection(
        self,
        original_sql: str,
        raw_result: Any,
        policy_decision: PolicyDecision,
        analysis_result: AnalysisResult
    ) -> Dict[str, Any]:
        """应用去标识化保护"""
        params = policy_decision.params
        columns = params.get("columns", [])
        
        # 确保结果是列表格式
        if isinstance(raw_result, list):
            protected_result = self.deid_rewriter.apply_deid(raw_result, columns)
        else:
            protected_result = raw_result
        
        # 构建响应
        return {
            "type": "DeID",
            "original_query": original_sql,
            "protected_result": protected_result,
            "privacy_info": self.deid_rewriter.create_privacy_info(columns)
        }
    
    def _create_pass_response(
        self,
        original_sql: str,
        raw_result: Any
    ) -> Dict[str, Any]:
        """创建透传响应"""
        return {
            "type": "PASS",
            "original_query": original_sql,
            "protected_result": raw_result,
            "privacy_info": {"method": "None", "reason": "No protection required"}
        }
    
    def _create_error_response(
        self,
        original_sql: str,
        reason: str
    ) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "type": "ERROR",
            "original_query": original_sql,
            "protected_result": None,
            "error": reason,
        }

