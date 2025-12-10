"""
DeIDRewriter - 去标识化重写器
职责: 对非聚合查询的敏感列进行脱敏
"""
from typing import Any, Dict, List

from .methods import hash_value, mask_email, mask_phone, mask_name, generalize_age


class DeIDRewriter:
    """去标识化重写器"""
    
    # 默认敏感列及其脱敏方法映射
    DEFAULT_SENSITIVE_COLUMNS = {
        "name": "mask_name",
        "email": "mask_email", 
        "phone": "mask_phone",
        "mobile": "mask_phone",
        "age": "generalize_age",
        "id_card": "hash",
        "ssn": "hash",
        "password": "hash",
    }
    
    # 可用的脱敏方法
    METHODS = {
        "hash": hash_value,
        "mask_email": mask_email,
        "mask_phone": mask_phone,
        "mask_name": mask_name,
        "generalize_age": generalize_age,
    }
    
    def __init__(self, sensitive_columns: Dict[str, str] = None):
        """
        初始化去标识化重写器
        
        Args:
            sensitive_columns: 敏感列及其脱敏方法映射
        """
        self.sensitive_columns = sensitive_columns or self.DEFAULT_SENSITIVE_COLUMNS.copy()
    
    def apply_deid(
        self,
        rows: List[Dict[str, Any]],
        columns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        对查询结果集应用去标识化
        
        Args:
            rows: 查询结果行列表
            columns: 需要处理的列名 (None表示自动检测)
            
        Returns:
            脱敏后的结果集
        """
        if not rows:
            return rows
        
        # 自动检测需要脱敏的列
        if columns is None:
            columns = list(rows[0].keys()) if rows else []
        
        # 处理每一行
        result = []
        for row in rows:
            new_row = dict(row)
            for col in columns:
                if col.lower() in self.sensitive_columns:
                    method_name = self.sensitive_columns[col.lower()]
                    method = self.METHODS.get(method_name, hash_value)
                    new_row[col] = method(row.get(col))
            result.append(new_row)
        
        return result
    
    def add_sensitive_column(self, column: str, method: str = "hash"):
        """添加敏感列配置"""
        self.sensitive_columns[column.lower()] = method
    
    def create_privacy_info(self, columns_processed: List[str]) -> Dict[str, Any]:
        """生成隐私信息元数据"""
        methods_used = {}
        for col in columns_processed:
            if col.lower() in self.sensitive_columns:
                methods_used[col] = self.sensitive_columns[col.lower()]
        
        return {
            "method": "DeIdentification",
            "columns_processed": columns_processed,
            "methods_used": methods_used,
        }

