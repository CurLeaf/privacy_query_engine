"""
QueryExecutor - 查询执行器
职责: 协调查询执行和隐私保护处理

支持两种执行模式:
1. ORM 模式: 使用 SQLModel 实体进行类型安全的查询
2. SQL 模式: 执行原始 SQL 语句
"""
from typing import Any, Dict, List, Optional, Type, TypeVar, Sequence, Union
from enum import Enum
from dataclasses import dataclass, field

from sqlmodel import SQLModel, select

from ..analyzer import AnalysisResult
from ..policy import PolicyDecision
from ..privacy import DPRewriter, DeIDRewriter
from ..core.context import QueryContext
from .mock import MockDatabaseExecutor
from .database import DatabaseConnection

# 泛型类型变量
T = TypeVar("T", bound=SQLModel)


class ExecutionMode(str, Enum):
    """执行模式枚举"""
    ORM = "orm"      # ORM 模式
    SQL = "sql"      # 原始 SQL 模式
    MOCK = "mock"    # Mock 模式 (开发测试)


@dataclass
class QueryResult:
    """
    统一查询结果
    
    Attributes:
        success: 是否执行成功
        data: 查询结果数据
        row_count: 影响/返回的行数
        privacy_applied: 是否应用了隐私保护
        privacy_info: 隐私保护详情
        error: 错误信息 (如果有)
        original_query: 原始查询
        execution_mode: 执行模式
    """
    success: bool = True
    data: Any = None
    row_count: int = 0
    privacy_applied: bool = False
    privacy_info: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    original_query: str = ""
    execution_mode: str = "sql"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "data": self.data,
            "row_count": self.row_count,
            "privacy_applied": self.privacy_applied,
            "privacy_info": self.privacy_info,
            "error": self.error,
            "original_query": self.original_query,
            "execution_mode": self.execution_mode,
        }


class QueryExecutor:
    """
    查询执行器
    
    整合数据库操作与隐私保护，提供统一的查询执行接口。
    
    使用示例:
        # 创建执行器
        executor = QueryExecutor.create(
            host="localhost",
            database="privacy",
            user="postgres",
            password="123456"
        )
        
        # ORM 模式查询
        users = executor.get_all(User)
        user = executor.get_by_id(User, 1)
        
        # SQL 模式查询
        result = executor.execute_sql("SELECT * FROM users WHERE age > 18")
        
        # 带隐私保护的查询
        result = executor.execute_with_privacy(
            sql="SELECT COUNT(*) FROM users",
            analysis_result=analysis,
            policy_decision=policy
        )
    """
    
    def __init__(
        self,
        db_connection: DatabaseConnection = None,
        mode: ExecutionMode = ExecutionMode.SQL,
    ):
        """
        初始化查询执行器
        
        Args:
            db_connection: 数据库连接实例
            mode: 执行模式 (ORM/SQL/MOCK)
        """
        self.db = db_connection
        self.mode = mode
        self.mock_executor = MockDatabaseExecutor() if mode == ExecutionMode.MOCK else None
        
        # 隐私处理器
        self.dp_rewriter = DPRewriter()
        self.deid_rewriter = DeIDRewriter()
    
    @classmethod
    def create(
        cls,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        mode: ExecutionMode = ExecutionMode.SQL,
        **kwargs
    ) -> "QueryExecutor":
        """
        工厂方法: 创建查询执行器
        
        Args:
            host: 数据库主机
            port: 端口号
            database: 数据库名
            user: 用户名
            password: 密码
            mode: 执行模式
            **kwargs: 其他数据库连接参数
            
        Returns:
            QueryExecutor 实例
        """
        if mode == ExecutionMode.MOCK:
            return cls(db_connection=None, mode=mode)
        
        db = DatabaseConnection(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            **kwargs
        )
        return cls(db_connection=db, mode=mode)
    
    @classmethod
    def from_env(cls, mode: ExecutionMode = ExecutionMode.SQL, **kwargs) -> "QueryExecutor":
        """
        从环境变量创建执行器
        
        环境变量: PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
        """
        if mode == ExecutionMode.MOCK:
            return cls(db_connection=None, mode=mode)
        
        db = DatabaseConnection.from_env(**kwargs)
        return cls(db_connection=db, mode=mode)
    
    # ==================== ORM 查询方法 ====================
    
    def get_by_id(self, model: Type[T], id: int) -> Optional[T]:
        """
        根据 ID 获取单个实体
        
        Args:
            model: SQLModel 模型类
            id: 主键 ID
            
        Returns:
            模型实例或 None
        """
        self._ensure_db_connection()
        return self.db.get(model, id)
    
    def get_all(self, model: Type[T]) -> Sequence[T]:
        """
        获取模型的所有记录
        
        Args:
            model: SQLModel 模型类
            
        Returns:
            模型实例列表
        """
        self._ensure_db_connection()
        return self.db.get_all(model)
    
    def get_by_field(self, model: Type[T], field_name: str, value: Any) -> Sequence[T]:
        """
        根据字段值查询
        
        Args:
            model: SQLModel 模型类
            field_name: 字段名
            value: 字段值
            
        Returns:
            匹配的模型实例列表
        """
        self._ensure_db_connection()
        return self.db.get_by_field(model, field_name, value)
    
    def get_one(self, model: Type[T], field_name: str, value: Any) -> Optional[T]:
        """
        根据字段值查询单个记录
        
        Args:
            model: SQLModel 模型类
            field_name: 字段名
            value: 字段值
            
        Returns:
            匹配的模型实例或 None
        """
        self._ensure_db_connection()
        return self.db.get_one_by_field(model, field_name, value)
    
    def query(self, statement) -> Sequence[Any]:
        """
        执行自定义 SQLModel select 语句
        
        Args:
            statement: select 语句
            
        Returns:
            查询结果列表
            
        Example:
            from sqlmodel import select
            stmt = select(User).where(User.age > 18)
            users = executor.query(stmt)
        """
        self._ensure_db_connection()
        return self.db.query(statement)
    
    def query_one(self, statement) -> Optional[Any]:
        """
        执行自定义 select 语句，返回单个结果
        
        Args:
            statement: select 语句
            
        Returns:
            单个查询结果或 None
        """
        self._ensure_db_connection()
        return self.db.query_one(statement)
    
    def count(self, model: Type[T]) -> int:
        """
        统计模型记录数
        
        Args:
            model: SQLModel 模型类
            
        Returns:
            记录数量
        """
        self._ensure_db_connection()
        return self.db.count(model)
    
    # ==================== ORM 写入方法 ====================
    
    def add(self, obj: T) -> T:
        """
        添加单个实体
        
        Args:
            obj: SQLModel 模型实例
            
        Returns:
            添加后的对象（包含生成的 ID）
        """
        self._ensure_db_connection()
        return self.db.add(obj)
    
    def add_all(self, objects: List[T]) -> List[T]:
        """
        批量添加实体
        
        Args:
            objects: 模型实例列表
            
        Returns:
            添加后的对象列表
        """
        self._ensure_db_connection()
        return self.db.add_all(objects)
    
    def update(self, obj: T, **kwargs) -> T:
        """
        更新实体
        
        Args:
            obj: SQLModel 模型实例
            **kwargs: 要更新的字段和值
            
        Returns:
            更新后的对象
        """
        self._ensure_db_connection()
        return self.db.update(obj, **kwargs)
    
    def delete(self, obj: T) -> bool:
        """
        删除实体
        
        Args:
            obj: SQLModel 模型实例
            
        Returns:
            是否删除成功
        """
        self._ensure_db_connection()
        return self.db.delete(obj)
    
    def delete_by_id(self, model: Type[T], id: int) -> bool:
        """
        根据 ID 删除实体
        
        Args:
            model: SQLModel 模型类
            id: 主键 ID
            
        Returns:
            是否删除成功
        """
        self._ensure_db_connection()
        return self.db.delete_by_id(model, id)
    
    # ==================== 原始 SQL 执行方法 ====================
    
    def execute_sql(
        self,
        sql: str,
        params: Dict[str, Any] = None
    ) -> QueryResult:
        """
        执行原始 SQL 查询
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
            
        Returns:
            QueryResult 查询结果
        """
        try:
            if self.mode == ExecutionMode.MOCK and self.mock_executor:
                data = self.mock_executor.execute(sql)
                return QueryResult(
                    success=True,
                    data=data,
                    row_count=len(data) if isinstance(data, list) else 1,
                    original_query=sql,
                    execution_mode="mock"
                )
            
            self._ensure_db_connection()
            
            # 判断查询类型
            sql_upper = sql.strip().upper()
            
            if sql_upper.startswith("SELECT"):
                # 检查是否是聚合查询
                if self._is_aggregate_query(sql_upper):
                    data = self.db.execute_scalar(sql, params)
                    return QueryResult(
                        success=True,
                        data=data,
                        row_count=1,
                        original_query=sql,
                        execution_mode="sql"
                    )
                else:
                    data = self.db.execute_query(sql, params)
                    return QueryResult(
                        success=True,
                        data=data,
                        row_count=len(data),
                        original_query=sql,
                        execution_mode="sql"
                    )
            else:
                # INSERT/UPDATE/DELETE/TRUNCATE 等
                row_count = self.db.execute(sql, params)
                return QueryResult(
                    success=True,
                    data=None,
                    row_count=row_count,
                    original_query=sql,
                    execution_mode="sql"
                )
                
        except Exception as e:
            return QueryResult(
                success=False,
                error=str(e),
                original_query=sql,
                execution_mode=self.mode.value
            )
    
    def execute_scalar(self, sql: str, params: Dict[str, Any] = None) -> Any:
        """
        执行查询并返回单个值
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
            
        Returns:
            单个查询结果值
        """
        if self.mode == ExecutionMode.MOCK and self.mock_executor:
            return self.mock_executor.execute(sql)
        
        self._ensure_db_connection()
        return self.db.execute_scalar(sql, params)
    
    def execute_query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询并返回结果列表
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
            
        Returns:
            查询结果列表 (每行为字典)
        """
        if self.mode == ExecutionMode.MOCK and self.mock_executor:
            return self.mock_executor.execute(sql)
        
        self._ensure_db_connection()
        return self.db.execute_query(sql, params)
    
    # ==================== 隐私保护执行方法 ====================
    
    def execute_with_privacy(
        self,
        sql: str,
        analysis_result: AnalysisResult,
        policy_decision: PolicyDecision,
        context: QueryContext = None,
    ) -> QueryResult:
        """
        执行查询并应用隐私保护
        
        Args:
            sql: 原始 SQL 语句
            analysis_result: SQL 分析结果
            policy_decision: 策略决策
            context: 查询上下文
            
        Returns:
            QueryResult 包含隐私保护的查询结果
        """
        # Step 1: 检查是否被拒绝
        if policy_decision.action == "REJECT":
            return QueryResult(
                success=False,
                error=policy_decision.reason,
                original_query=sql,
                execution_mode=self.mode.value
            )
        
        # Step 2: 执行原始查询
        result = self.execute_sql(sql)
        if not result.success:
            return result
        
        raw_data = result.data
        
        # Step 3: 根据策略应用隐私保护
        if policy_decision.action == "DP":
            return self._apply_dp_protection(sql, raw_data, policy_decision)
        elif policy_decision.action == "DeID":
            return self._apply_deid_protection(sql, raw_data, policy_decision, analysis_result)
        else:
            # PASS: 不需要隐私保护
            result.privacy_info = {"method": "None", "reason": "No protection required"}
            return result
    
    def execute(
        self,
        original_sql: str,
        analysis_result: AnalysisResult,
        policy_decision: PolicyDecision,
        context: QueryContext = None,
    ) -> Dict[str, Any]:
        """
        执行查询并应用隐私保护 (兼容旧接口)
        
        Args:
            original_sql: 原始SQL
            analysis_result: SQL分析结果
            policy_decision: 策略决策
            context: 查询上下文
            
        Returns:
            统一响应格式的结果 (字典)
        """
        result = self.execute_with_privacy(
            sql=original_sql,
            analysis_result=analysis_result,
            policy_decision=policy_decision,
            context=context
        )
        
        # 转换为旧格式响应
        if not result.success:
            return {
                "type": "ERROR",
                "original_query": original_sql,
                "protected_result": None,
                "error": result.error,
            }
        
        response_type = "PASS"
        if result.privacy_applied:
            response_type = result.privacy_info.get("type", "PASS")
        
        return {
            "type": response_type,
            "original_query": original_sql,
            "protected_result": result.data,
            "privacy_info": result.privacy_info,
        }
    
    # ==================== 数据库管理方法 ====================
    
    def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        if self.mode == ExecutionMode.MOCK:
            return {"status": "mock", "message": "Using mock executor"}
        
        self._ensure_db_connection()
        return self.db.test_connection()
    
    def get_tables(self) -> List[str]:
        """获取所有表名"""
        self._ensure_db_connection()
        return self.db.get_tables()
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        self._ensure_db_connection()
        return self.db.get_table_columns(table_name)
    
    def create_tables(self):
        """创建所有 SQLModel 定义的表"""
        self._ensure_db_connection()
        self.db.create_tables()
    
    def drop_tables(self):
        """删除所有 SQLModel 定义的表"""
        self._ensure_db_connection()
        self.db.drop_tables()
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()
    
    def __enter__(self):
        """支持 with 语句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭连接"""
        self.close()
    
    # ==================== 私有方法 ====================
    
    def _ensure_db_connection(self):
        """确保数据库连接可用"""
        if self.db is None:
            raise RuntimeError(
                "No database connection available. "
                "Use QueryExecutor.create() or provide a DatabaseConnection."
            )
    
    def _is_aggregate_query(self, sql_upper: str) -> bool:
        """判断是否是聚合查询"""
        aggregates = ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]
        return any(agg in sql_upper for agg in aggregates)
    
    def _apply_dp_protection(
        self,
        sql: str,
        raw_data: Any,
        policy_decision: PolicyDecision
    ) -> QueryResult:
        """应用差分隐私保护"""
        params = policy_decision.params
        epsilon = params.get("epsilon", 1.0)
        mechanism = params.get("mechanism", "laplace")
        sensitivity = params.get("sensitivity", 1.0)
        
        # 添加噪声
        protected_data = self.dp_rewriter.apply_dp(
            raw_data, epsilon, sensitivity, mechanism
        )
        
        return QueryResult(
            success=True,
            data=protected_data,
            row_count=1,
            privacy_applied=True,
            privacy_info={
                "type": "DP",
                "epsilon": epsilon,
                "method": mechanism.capitalize(),
                "sensitivity": sensitivity,
            },
            original_query=sql,
            execution_mode=self.mode.value
        )
    
    def _apply_deid_protection(
        self,
        sql: str,
        raw_data: Any,
        policy_decision: PolicyDecision,
        analysis_result: AnalysisResult
    ) -> QueryResult:
        """应用去标识化保护"""
        params = policy_decision.params
        columns = params.get("columns", [])
        
        # 确保结果是列表格式
        if isinstance(raw_data, list):
            protected_data = self.deid_rewriter.apply_deid(raw_data, columns)
            row_count = len(protected_data)
        else:
            protected_data = raw_data
            row_count = 1
        
        return QueryResult(
            success=True,
            data=protected_data,
            row_count=row_count,
            privacy_applied=True,
            privacy_info={
                "type": "DeID",
                **self.deid_rewriter.create_privacy_info(columns)
            },
            original_query=sql,
            execution_mode=self.mode.value
        )
