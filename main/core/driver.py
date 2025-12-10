"""
QueryDriver - 核心控制器
职责: 接收原始SQL，协调分析和重写，返回隐私保护后的结果
"""
from typing import Any, Dict, Optional

from ..analyzer import SQLAnalyzer, AnalysisResult
from ..policy import PolicyEngine
from ..executor import QueryExecutor, ExecutionMode, DatabaseConnection
from .context import QueryContext


class QueryDriver:
    """
    查询驱动器 - 系统核心控制器
    
    协调 SQL 分析、策略决策、隐私保护执行的完整流程。
    
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
    """
    
    def __init__(
        self,
        analyzer: SQLAnalyzer = None,
        policy_engine: PolicyEngine = None,
        executor: QueryExecutor = None,
        use_mock: bool = True,
    ):
        """
        初始化 QueryDriver
        
        Args:
            analyzer: SQL 分析器实例
            policy_engine: 策略引擎实例
            executor: 查询执行器实例
            use_mock: 是否使用 Mock 模式 (默认 True)
        """
        self.analyzer = analyzer or SQLAnalyzer()
        self.policy_engine = policy_engine or PolicyEngine()
        
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
        
        return cls(
            executor=executor,
            policy_engine=policy_engine,
            use_mock=False,
        )
    
    @classmethod
    def from_env(cls, policy_config_path: str = None, **kwargs) -> "QueryDriver":
        """
        从环境变量创建 QueryDriver
        
        环境变量: PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
        """
        executor = QueryExecutor.from_env(mode=ExecutionMode.SQL, **kwargs)
        policy_engine = PolicyEngine(config_path=policy_config_path) if policy_config_path else PolicyEngine()
        
        return cls(
            executor=executor,
            policy_engine=policy_engine,
            use_mock=False,
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

