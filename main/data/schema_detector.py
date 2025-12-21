"""
SchemaDetector - 自动检测数据模式和敏感列

无需预定义表结构，自动识别列类型和敏感度。
"""
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


class ColumnType(Enum):
    """列数据类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    EMAIL = "email"
    PHONE = "phone"
    ID_CARD = "id_card"
    ADDRESS = "address"
    NAME = "name"
    UNKNOWN = "unknown"


class SensitivityLevel(Enum):
    """敏感度级别"""
    PUBLIC = "public"           # 公开数据
    INTERNAL = "internal"       # 内部数据
    SENSITIVE = "sensitive"     # 敏感数据
    HIGHLY_SENSITIVE = "highly_sensitive"  # 高度敏感


@dataclass
class ColumnSchema:
    """列模式信息"""
    name: str
    data_type: ColumnType
    sensitivity: SensitivityLevel
    nullable: bool = True
    unique_ratio: float = 0.0  # 唯一值比例
    sample_values: List[Any] = field(default_factory=list)
    recommended_method: str = "none"  # 推荐的脱敏方法


@dataclass
class DataSchema:
    """数据模式"""
    columns: Dict[str, ColumnSchema] = field(default_factory=dict)
    row_count: int = 0
    quasi_identifiers: List[str] = field(default_factory=list)
    sensitive_attributes: List[str] = field(default_factory=list)
    direct_identifiers: List[str] = field(default_factory=list)


class SchemaDetector:
    """
    数据模式自动检测器
    
    功能：
    - 自动检测列的数据类型
    - 识别敏感列（基于列名和数据模式）
    - 推荐脱敏方法
    - 识别准标识符和直接标识符
    """
    
    # 敏感列名模式
    SENSITIVE_PATTERNS = {
        # 直接标识符 - 高度敏感
        SensitivityLevel.HIGHLY_SENSITIVE: [
            r"^(id_card|idcard|identity|ssn|social_security).*$",
            r"^(passport|driver_license|license_no).*$",
            r"^(bank_account|credit_card|card_no|card_number).*$",
            r"^(password|passwd|pwd|secret|token).*$",
        ],
        # 敏感数据
        SensitivityLevel.SENSITIVE: [
            r"^(name|full_name|first_name|last_name|username).*$",
            r"^(email|mail|e_mail).*$",
            r"^(phone|mobile|tel|telephone|cell).*$",
            r"^(address|addr|street|location|home_address).*$",
            r"^(salary|income|wage|payment|balance).*$",
            r"^(medical|health|diagnosis|disease).*$",
            r"^(dob|birth|birthday|date_of_birth).*$",
        ],
        # 准标识符 - 内部数据
        SensitivityLevel.INTERNAL: [
            r"^(age|gender|sex).*$",
            r"^(zip|zipcode|postal|postcode).*$",
            r"^(city|state|province|country|region).*$",
            r"^(education|degree|occupation|job).*$",
            r"^(marital|marriage).*$",
        ],
    }
    
    # 数据类型检测模式
    TYPE_PATTERNS = {
        ColumnType.EMAIL: r"^[\w\.-]+@[\w\.-]+\.\w+$",
        ColumnType.PHONE: r"^[\d\-\+\(\)\s]{7,20}$",
        ColumnType.ID_CARD: r"^\d{15}(\d{2}[\dXx])?$",  # 中国身份证
        ColumnType.DATE: r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$",
        ColumnType.DATETIME: r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}[\sT]\d{1,2}:\d{1,2}",
    }
    
    # 脱敏方法推荐
    METHOD_RECOMMENDATIONS = {
        ColumnType.EMAIL: "mask_email",
        ColumnType.PHONE: "mask_phone",
        ColumnType.NAME: "mask_name",
        ColumnType.ID_CARD: "hash",
        ColumnType.ADDRESS: "geographic_generalize",
        ColumnType.DATE: "date_shift",
        ColumnType.DATETIME: "date_shift",
    }
    
    SENSITIVITY_METHOD_RECOMMENDATIONS = {
        SensitivityLevel.HIGHLY_SENSITIVE: "hash",
        SensitivityLevel.SENSITIVE: "mask",
        SensitivityLevel.INTERNAL: "generalize",
        SensitivityLevel.PUBLIC: "none",
    }
    
    def detect(self, data: List[Dict[str, Any]], sample_size: int = 100) -> DataSchema:
        """
        检测数据模式
        
        Args:
            data: 数据列表
            sample_size: 用于检测的样本大小
            
        Returns:
            DataSchema 数据模式
        """
        if not data:
            return DataSchema()
        
        schema = DataSchema(row_count=len(data))
        sample = data[:sample_size]
        
        # 获取所有列名
        all_columns: Set[str] = set()
        for row in sample:
            all_columns.update(row.keys())
        
        # 分析每一列
        for col_name in all_columns:
            col_schema = self._analyze_column(col_name, sample)
            schema.columns[col_name] = col_schema
            
            # 分类
            if col_schema.sensitivity == SensitivityLevel.HIGHLY_SENSITIVE:
                schema.direct_identifiers.append(col_name)
            elif col_schema.sensitivity == SensitivityLevel.SENSITIVE:
                schema.sensitive_attributes.append(col_name)
            elif col_schema.sensitivity == SensitivityLevel.INTERNAL:
                schema.quasi_identifiers.append(col_name)
        
        return schema
    
    def _analyze_column(self, col_name: str, sample: List[Dict]) -> ColumnSchema:
        """分析单列"""
        values = [row.get(col_name) for row in sample if col_name in row]
        non_null_values = [v for v in values if v is not None and v != ""]
        
        # 检测数据类型
        data_type = self._detect_type(col_name, non_null_values)
        
        # 检测敏感度
        sensitivity = self._detect_sensitivity(col_name, data_type)
        
        # 计算唯一值比例
        unique_ratio = len(set(non_null_values)) / len(non_null_values) if non_null_values else 0
        
        # 推荐脱敏方法
        method = self._recommend_method(data_type, sensitivity)
        
        return ColumnSchema(
            name=col_name,
            data_type=data_type,
            sensitivity=sensitivity,
            nullable=len(non_null_values) < len(values),
            unique_ratio=unique_ratio,
            sample_values=non_null_values[:5],
            recommended_method=method,
        )
    
    def _detect_type(self, col_name: str, values: List[Any]) -> ColumnType:
        """检测列数据类型"""
        if not values:
            return ColumnType.UNKNOWN
        
        # 先根据列名推断
        col_lower = col_name.lower()
        if any(kw in col_lower for kw in ["email", "mail"]):
            return ColumnType.EMAIL
        if any(kw in col_lower for kw in ["phone", "mobile", "tel"]):
            return ColumnType.PHONE
        if any(kw in col_lower for kw in ["name", "username"]):
            return ColumnType.NAME
        if any(kw in col_lower for kw in ["address", "addr", "street"]):
            return ColumnType.ADDRESS
        if any(kw in col_lower for kw in ["id_card", "idcard", "identity"]):
            return ColumnType.ID_CARD
        
        # 根据值模式检测
        str_values = [str(v) for v in values if v is not None]
        if str_values:
            sample_val = str_values[0]
            for dtype, pattern in self.TYPE_PATTERNS.items():
                if re.match(pattern, sample_val):
                    return dtype
        
        # 根据值类型检测
        type_counts = {}
        for v in values:
            if isinstance(v, bool):
                t = ColumnType.BOOLEAN
            elif isinstance(v, int):
                t = ColumnType.INTEGER
            elif isinstance(v, float):
                t = ColumnType.FLOAT
            elif isinstance(v, str):
                t = ColumnType.STRING
            else:
                t = ColumnType.UNKNOWN
            type_counts[t] = type_counts.get(t, 0) + 1
        
        if type_counts:
            return max(type_counts, key=type_counts.get)
        
        return ColumnType.UNKNOWN
    
    def _detect_sensitivity(self, col_name: str, data_type: ColumnType) -> SensitivityLevel:
        """检测列敏感度"""
        col_lower = col_name.lower()
        
        # 根据列名模式匹配
        for level, patterns in self.SENSITIVE_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, col_lower):
                    return level
        
        # 根据数据类型推断
        if data_type in [ColumnType.EMAIL, ColumnType.PHONE, ColumnType.ID_CARD]:
            return SensitivityLevel.SENSITIVE
        if data_type == ColumnType.NAME:
            return SensitivityLevel.SENSITIVE
        if data_type == ColumnType.ADDRESS:
            return SensitivityLevel.SENSITIVE
        
        return SensitivityLevel.PUBLIC
    
    def _recommend_method(self, data_type: ColumnType, sensitivity: SensitivityLevel) -> str:
        """推荐脱敏方法"""
        # 优先根据数据类型推荐
        if data_type in self.METHOD_RECOMMENDATIONS:
            return self.METHOD_RECOMMENDATIONS[data_type]
        
        # 根据敏感度推荐
        return self.SENSITIVITY_METHOD_RECOMMENDATIONS.get(sensitivity, "none")
    
    def get_protection_plan(self, schema: DataSchema) -> Dict[str, Dict[str, Any]]:
        """
        生成保护计划
        
        Args:
            schema: 数据模式
            
        Returns:
            保护计划 {column_name: {method, params}}
        """
        plan = {}
        
        for col_name, col_schema in schema.columns.items():
            if col_schema.sensitivity in [SensitivityLevel.SENSITIVE, SensitivityLevel.HIGHLY_SENSITIVE]:
                plan[col_name] = {
                    "method": col_schema.recommended_method,
                    "sensitivity": col_schema.sensitivity.value,
                    "data_type": col_schema.data_type.value,
                }
        
        return plan
