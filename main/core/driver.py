"""
QueryDriver - 核心控制器
职责: 接收原始SQL，协调分析和重写，返回隐私保护后的结果
"""
from typing import Any, Dict, Optional

from ..analyzer import SQLAnalyzer, AnalysisResult
from ..policy import PolicyEngine
from ..executor import QueryExecutor, ExecutionMode, DatabaseConnection
from ..budget import PrivacyBudgetManager, BudgetCheckResult
from .context import QueryContext


class QueryDriver:
    """
    查询驱动器 - 系统核心控制器
    
    协调 SQL 分析、策略决策、隐私保护执行的完整流程。
    支持 v2.0 特性：隐私预算管理、增强SQL分析、多表敏感度计算。
    
    使用示例:
        # Mock 模式 (开发测试)
        driver = QueryDriver()
        
        # 真实数据库模式
        driver = QueryDriver.create(
            host="localhost",
            database="privacy",
            user="postgres",
            password="123456"
        )
        
        # 处理查询
        result = driver.process_query("SELECT COUNT(*) FROM users")
        
        # 带预算管理的查询
        result = driver.process_query(
            "SELECT COUNT(*) FROM users",
            context=QueryContext(user_id="user123")
        )
    """
    
    def __init__(
        self,
        analyzer: SQLAnalyzer = None,
        policy_engine: PolicyEngine = None,
        executor: QueryExecutor = None,
        budget_manager: PrivacyBudgetManager = None,
        use_mock: bool = True,
        enable_budget_management: bool = False,
    ):
        """
        初始化 QueryDriver
        
        Args:
            analyzer: SQL 分析器实例
            policy_engine: 策略引擎实例
            executor: 查询执行器实例
            budget_manager: 隐私预算管理器实例 (v2.0)
            use_mock: 是否使用 Mock 模式 (默认 True)
            enable_budget_management: 是否启用预算管理 (v2.0)
        """
        self.analyzer = analyzer or SQLAnalyzer()
        self.policy_engine = policy_engine or PolicyEngine()
        self.enable_budget_management = enable_budget_management
        
        # 预算管理器 (v2.0)
        if budget_manager is not None:
            self.budget_manager = budget_manager
            self.enable_budget_management = True
        elif enable_budget_management:
            self.budget_manager = PrivacyBudgetManager()
        else:
            self.budget_manager = None
        
        # 如果没有提供 executor，根据 use_mock 创建默认实例
        if executor is not None:
            self.executor = executor
        else:
            mode = ExecutionMode.MOCK if use_mock else ExecutionMode.SQL
            self.executor = QueryExecutor.create(mode=mode)
    
    @classmethod
    def create(
        cls,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        policy_config_path: str = None,
        enable_budget_management: bool = False,
        default_budget: float = 1.0,
        **kwargs
    ) -> "QueryDriver":
        """
        工厂方法: 创建连接真实数据库的 QueryDriver
        
        Args:
            host: 数据库主机
            port: 端口号
            database: 数据库名
            user: 用户名
            password: 密码
            policy_config_path: 策略配置文件路径 (可选)
            enable_budget_management: 是否启用预算管理 (v2.0)
            default_budget: 默认预算 (v2.0)
            **kwargs: 其他数据库连接参数
            
        Returns:
            QueryDriver 实例
        """
        # 创建连接真实数据库的执行器
        executor = QueryExecutor.create(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            mode=ExecutionMode.SQL,
            **kwargs
        )
        
        # 创建策略引擎
        policy_engine = PolicyEngine(config_path=policy_config_path) if policy_config_path else PolicyEngine()
        
        # 创建预算管理器 (v2.0)
        budget_manager = None
        if enable_budget_management:
            budget_manager = PrivacyBudgetManager(default_budget=default_budget)
        
        return cls(
            executor=executor,
            policy_engine=policy_engine,
            budget_manager=budget_manager,
            use_mock=False,
            enable_budget_management=enable_budget_management,
        )
    
    @classmethod
    def from_env(cls, policy_config_path: str = None, enable_budget_management: bool = False, **kwargs) -> "QueryDriver":
        """
        从环境变量创建 QueryDriver
        
        环境变量: PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
        """
        executor = QueryExecutor.from_env(mode=ExecutionMode.SQL, **kwargs)
        policy_engine = PolicyEngine(config_path=policy_config_path) if policy_config_path else PolicyEngine()
        
        budget_manager = None
        if enable_budget_management:
            budget_manager = PrivacyBudgetManager()
        
        return cls(
            executor=executor,
            policy_engine=policy_engine,
            budget_manager=budget_manager,
            use_mock=False,
            enable_budget_management=enable_budget_management,
        )
    
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
        
        # Step 1: SQL Analysis - 分析SQL语义 (增强版支持JOIN/子查询/窗口函数)
        analysis_result = self.analyzer.analyze(original_sql)
        
        # Step 2: Policy Decision - 根据策略决定处理方式
        policy_decision = self.policy_engine.evaluate(analysis_result)
        
        # Step 2.5: Budget Check (v2.0) - 检查隐私预算
        if self.enable_budget_management and self.budget_manager:
            budget_result = self._check_and_consume_budget(context, policy_decision)
            if not budget_result.allowed:
                return {
                    "success": False,
                    "error": "insufficient_budget",
                    "message": budget_result.message,
                    "remaining_budget": budget_result.remaining_budget,
                    "requested_budget": budget_result.requested_budget,
                }
        
        # Step 3: Calculate Multi-Table Sensitivity (v2.0)
        if analysis_result.joins:
            sensitivity = self._calculate_multi_table_sensitivity(analysis_result)
            context.metadata["multi_table_sensitivity"] = sensitivity
        
        # Step 4: Execute & Apply Privacy Protection - 执行并应用隐私保护
        protected_result = self.executor.execute(
            original_sql=original_sql,
            analysis_result=analysis_result,
            policy_decision=policy_decision,
            context=context,
        )
        
        # 添加v2.0元数据
        if self.enable_budget_management and self.budget_manager and context.user_id:
            protected_result["budget_status"] = self.budget_manager.get_budget_status(context.user_id)
        
        return protected_result
    
    def _check_and_consume_budget(self, context: QueryContext, policy_decision) -> BudgetCheckResult:
        """检查并消耗隐私预算 (v2.0)"""
        user_id = context.user_id or "anonymous"
        
        # 从策略决策中获取epsilon值
        epsilon = getattr(policy_decision, 'epsilon', 0.1)
        if hasattr(policy_decision, 'params') and 'epsilon' in policy_decision.params:
            epsilon = policy_decision.params['epsilon']
        
        # 检查预算
        check_result = self.budget_manager.check_budget(user_id, epsilon)
        
        if check_result.allowed:
            # 消耗预算
            self.budget_manager.consume_budget(
                user_id=user_id,
                epsilon=epsilon,
                query_id=context.query_id,
                query_sql=context.metadata.get("original_sql"),
                privacy_mechanism=getattr(policy_decision, 'method', 'unknown')
            )
        
        return check_result
    
    def _calculate_multi_table_sensitivity(self, analysis_result: AnalysisResult) -> float:
        """计算多表查询的组合敏感度 (v2.0)"""
        base_sensitivity = 1.0
        
        # 每个JOIN增加敏感度
        join_factor = 1.0 + (len(analysis_result.joins) * 0.5)
        
        # 考虑JOIN类型
        for join in analysis_result.joins:
            if join.join_type in ("LEFT", "RIGHT", "FULL"):
                join_factor *= 1.2  # 外连接增加更多敏感度
        
        # 考虑子查询
        if analysis_result.subqueries:
            join_factor *= (1.0 + len(analysis_result.subqueries) * 0.3)
        
        # 考虑窗口函数
        if analysis_result.window_functions:
            join_factor *= (1.0 + len(analysis_result.window_functions) * 0.2)
        
        return base_sensitivity * join_factor
    
    def get_budget_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户预算状态 (v2.0)"""
        if not self.budget_manager:
            return None
        return self.budget_manager.get_budget_status(user_id)
    
    def reset_user_budget(self, user_id: str) -> bool:
        """重置用户预算 (v2.0)"""
        if not self.budget_manager:
            return False
        self.budget_manager.reset_budget(user_id)
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        return self.executor.test_connection()
    
    def close(self):
        """关闭数据库连接"""
        if self.executor:
            self.executor.close()
    
    def __enter__(self):
        """支持 with 语句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭连接"""
        self.close()

