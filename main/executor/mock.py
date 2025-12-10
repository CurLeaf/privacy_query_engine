"""
MockDatabaseExecutor - Mock数据库执行器
用于开发和测试阶段
"""
from typing import Any, Dict, List


class MockDatabaseExecutor:
    """Mock数据库执行器"""
    
    # Mock数据
    MOCK_DATA = {
        "users": [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 28, "phone": "13812345678"},
            {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 35, "phone": "13987654321"},
            {"id": 3, "name": "王五", "email": "wangwu@example.com", "age": 42, "phone": "13611112222"},
            {"id": 4, "name": "John Doe", "email": "john@example.com", "age": 30, "phone": "13522223333"},
            {"id": 5, "name": "Jane Smith", "email": "jane@example.com", "age": 25, "phone": "13633334444"},
        ],
        "orders": [
            {"id": 1, "user_id": 1, "amount": 100.0, "status": "completed"},
            {"id": 2, "user_id": 2, "amount": 250.5, "status": "pending"},
            {"id": 3, "user_id": 1, "amount": 75.0, "status": "completed"},
        ],
    }
    
    def __init__(self):
        self.data = self.MOCK_DATA.copy()
    
    def execute(self, sql: str) -> Any:
        """
        执行SQL查询 (Mock实现)
        
        Args:
            sql: SQL查询语句
            
        Returns:
            查询结果
        """
        sql_upper = sql.upper()
        
        # 处理COUNT查询
        if "COUNT(*)" in sql_upper:
            return self._handle_count(sql)
        
        # 处理SUM查询
        if "SUM(" in sql_upper:
            return self._handle_sum(sql)
        
        # 处理SELECT查询
        if sql_upper.startswith("SELECT"):
            return self._handle_select(sql)
        
        return None
    
    def _handle_count(self, sql: str) -> int:
        """处理COUNT查询"""
        table = self._extract_table(sql)
        if table and table in self.data:
            return len(self.data[table])
        return 0
    
    def _handle_sum(self, sql: str) -> float:
        """处理SUM查询"""
        table = self._extract_table(sql)
        if table == "orders":
            return sum(row["amount"] for row in self.data.get("orders", []))
        return 0.0
    
    def _handle_select(self, sql: str) -> List[Dict[str, Any]]:
        """处理SELECT查询"""
        table = self._extract_table(sql)
        if table and table in self.data:
            return self.data[table].copy()
        return []
    
    def _extract_table(self, sql: str) -> str:
        """从SQL中提取表名"""
        sql_upper = sql.upper()
        if "FROM " in sql_upper:
            parts = sql_upper.split("FROM ")
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0]
                # 返回小写表名
                return table_part.lower().rstrip(";")
        return None

