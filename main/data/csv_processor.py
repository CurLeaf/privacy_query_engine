"""
CSV Privacy Processor - CSV 文件隐私保护处理器

支持 CSV 文件和 DataFrame 的隐私保护处理。
"""
import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field

from .schema_detector import SchemaDetector, DataSchema, SensitivityLevel
from ..privacy.deid import (
    DeIDRewriter,
    hash_value,
    mask_email,
    mask_phone,
    mask_name,
    generalize_age,
    date_shift,
    geographic_generalize,
    KAnonymizer,
    LDiversifier,
)


@dataclass
class ProcessingConfig:
    """处理配置"""
    # 自动检测敏感列
    auto_detect: bool = True
    # 手动指定的敏感列及方法
    column_methods: Dict[str, str] = field(default_factory=dict)
    # K-匿名化参数
    k_anonymity: Optional[int] = None
    # L-多样性参数
    l_diversity: Optional[int] = None
    # 准标识符（用于K-匿名/L-多样性）
    quasi_identifiers: List[str] = field(default_factory=list)
    # 敏感属性（用于L-多样性）
    sensitive_attribute: Optional[str] = None
    # 日期偏移的ID列
    date_shift_id_column: Optional[str] = None
    # 泛化规则
    generalization_rules: Dict[str, Callable] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    data: List[Dict[str, Any]]
    original_row_count: int
    processed_row_count: int
    schema: Optional[DataSchema] = None
    columns_processed: List[str] = field(default_factory=list)
    methods_applied: Dict[str, str] = field(default_factory=dict)
    suppressed_rows: int = 0
    error: Optional[str] = None


class CSVPrivacyProcessor:
    """
    CSV 隐私保护处理器
    
    功能：
    - 读取 CSV 文件并自动检测敏感列
    - 应用多种脱敏方法
    - 支持 K-匿名化和 L-多样性
    - 输出处理后的 CSV
    
    使用示例：
        processor = CSVPrivacyProcessor()
        
        # 自动检测并处理
        result = processor.process_file("data.csv")
        
        # 手动指定脱敏方法
        result = processor.process_file(
            "data.csv",
            config=ProcessingConfig(
                column_methods={"email": "mask_email", "phone": "mask_phone"},
                k_anonymity=5,
                quasi_identifiers=["age", "zipcode"]
            )
        )
        
        # 保存结果
        processor.save_csv(result.data, "output.csv")
    """
    
    # 可用的脱敏方法
    METHODS = {
        "hash": hash_value,
        "mask_email": mask_email,
        "mask_phone": mask_phone,
        "mask_name": mask_name,
        "generalize_age": generalize_age,
        "geographic_generalize": geographic_generalize,
        "suppress": lambda x: "*SUPPRESSED*",
        "none": lambda x: x,
    }
    
    def __init__(self):
        self.schema_detector = SchemaDetector()
        self.deid_rewriter = DeIDRewriter()
    
    def process_file(
        self,
        file_path: Union[str, Path],
        config: ProcessingConfig = None,
        encoding: str = "utf-8",
    ) -> ProcessingResult:
        """
        处理 CSV 文件
        
        Args:
            file_path: CSV 文件路径
            config: 处理配置
            encoding: 文件编码
            
        Returns:
            ProcessingResult 处理结果
        """
        config = config or ProcessingConfig()
        
        try:
            # 读取 CSV
            data = self._read_csv(file_path, encoding)
            if not data:
                return ProcessingResult(
                    success=False,
                    data=[],
                    original_row_count=0,
                    processed_row_count=0,
                    error="Empty file or failed to read"
                )
            
            # 处理数据
            return self.process_data(data, config)
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                data=[],
                original_row_count=0,
                processed_row_count=0,
                error=str(e)
            )
    
    def process_data(
        self,
        data: List[Dict[str, Any]],
        config: ProcessingConfig = None,
    ) -> ProcessingResult:
        """
        处理数据列表
        
        Args:
            data: 数据列表
            config: 处理配置
            
        Returns:
            ProcessingResult 处理结果
        """
        config = config or ProcessingConfig()
        original_count = len(data)
        
        # 检测数据模式
        schema = self.schema_detector.detect(data) if config.auto_detect else None
        
        # 确定要处理的列和方法
        column_methods = self._determine_methods(schema, config)
        
        # 复制数据
        result_data = [row.copy() for row in data]
        
        # 应用脱敏方法
        result_data = self._apply_methods(result_data, column_methods, config)
        
        # 应用 K-匿名化
        suppressed = 0
        if config.k_anonymity and config.quasi_identifiers:
            result_data, suppressed = self._apply_k_anonymity(
                result_data, config.k_anonymity, config.quasi_identifiers,
                config.generalization_rules
            )
        
        # 应用 L-多样性
        if config.l_diversity and config.quasi_identifiers and config.sensitive_attribute:
            result_data = self._apply_l_diversity(
                result_data, config.l_diversity,
                config.quasi_identifiers, config.sensitive_attribute
            )
        
        return ProcessingResult(
            success=True,
            data=result_data,
            original_row_count=original_count,
            processed_row_count=len(result_data),
            schema=schema,
            columns_processed=list(column_methods.keys()),
            methods_applied=column_methods,
            suppressed_rows=suppressed,
        )
    
    def _read_csv(self, file_path: Union[str, Path], encoding: str) -> List[Dict[str, Any]]:
        """读取 CSV 文件"""
        with open(file_path, "r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _determine_methods(
        self,
        schema: Optional[DataSchema],
        config: ProcessingConfig,
    ) -> Dict[str, str]:
        """确定每列的脱敏方法"""
        methods = {}
        
        # 从配置中获取手动指定的方法
        methods.update(config.column_methods)
        
        # 从自动检测的模式中获取推荐方法
        if schema and config.auto_detect:
            for col_name, col_schema in schema.columns.items():
                if col_name not in methods:
                    if col_schema.sensitivity in [SensitivityLevel.SENSITIVE, SensitivityLevel.HIGHLY_SENSITIVE]:
                        methods[col_name] = col_schema.recommended_method
        
        return methods
    
    def _apply_methods(
        self,
        data: List[Dict[str, Any]],
        column_methods: Dict[str, str],
        config: ProcessingConfig,
    ) -> List[Dict[str, Any]]:
        """应用脱敏方法"""
        for row in data:
            for col_name, method_name in column_methods.items():
                if col_name not in row:
                    continue
                
                value = row[col_name]
                if value is None or value == "":
                    continue
                
                # 获取脱敏方法
                method = self.METHODS.get(method_name)
                if not method:
                    continue
                
                # 特殊处理日期偏移
                if method_name == "date_shift" and config.date_shift_id_column:
                    id_value = row.get(config.date_shift_id_column, str(hash(str(row))))
                    row[col_name] = date_shift(value, str(id_value))
                # 特殊处理年龄泛化
                elif method_name == "generalize_age":
                    try:
                        row[col_name] = generalize_age(int(value))
                    except (ValueError, TypeError):
                        row[col_name] = value
                else:
                    row[col_name] = method(value)
        
        return data
    
    def _apply_k_anonymity(
        self,
        data: List[Dict[str, Any]],
        k: int,
        quasi_identifiers: List[str],
        generalization_rules: Dict[str, Callable],
    ) -> tuple:
        """应用 K-匿名化"""
        anonymizer = KAnonymizer(k=k)
        
        # 默认泛化规则
        default_rules = {
            "age": lambda x: generalize_age(int(x)) if x else x,
        }
        rules = {**default_rules, **generalization_rules}
        
        result = anonymizer.anonymize(data, quasi_identifiers, rules)
        
        # 统计被抑制的行数
        suppressed = sum(
            1 for row in result
            if any(row.get(qi) == "*SUPPRESSED*" for qi in quasi_identifiers)
        )
        
        return result, suppressed
    
    def _apply_l_diversity(
        self,
        data: List[Dict[str, Any]],
        l: int,
        quasi_identifiers: List[str],
        sensitive_attribute: str,
    ) -> List[Dict[str, Any]]:
        """应用 L-多样性"""
        diversifier = LDiversifier(l=l)
        return diversifier.diversify(data, quasi_identifiers, sensitive_attribute)
    
    def save_csv(
        self,
        data: List[Dict[str, Any]],
        file_path: Union[str, Path],
        encoding: str = "utf-8",
    ):
        """保存为 CSV 文件"""
        if not data:
            return
        
        fieldnames = list(data[0].keys())
        
        with open(file_path, "w", encoding=encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def to_csv_string(self, data: List[Dict[str, Any]]) -> str:
        """转换为 CSV 字符串"""
        if not data:
            return ""
        
        output = io.StringIO()
        fieldnames = list(data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()


class DataFrameProcessor:
    """
    DataFrame 隐私保护处理器
    
    支持 pandas DataFrame 的处理（可选依赖）
    """
    
    def __init__(self):
        self.csv_processor = CSVPrivacyProcessor()
    
    def process(
        self,
        df,  # pandas.DataFrame
        config: ProcessingConfig = None,
    ) -> ProcessingResult:
        """
        处理 DataFrame
        
        Args:
            df: pandas DataFrame
            config: 处理配置
            
        Returns:
            ProcessingResult 处理结果
        """
        # 转换为字典列表
        data = df.to_dict("records")
        
        # 使用 CSV 处理器处理
        return self.csv_processor.process_data(data, config)
    
    def to_dataframe(self, result: ProcessingResult):
        """
        将处理结果转换为 DataFrame
        
        Args:
            result: 处理结果
            
        Returns:
            pandas DataFrame
        """
        try:
            import pandas as pd
            return pd.DataFrame(result.data)
        except ImportError:
            raise ImportError("pandas is required for DataFrame operations")
