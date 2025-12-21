"""
Privacy-Preserving Data Export (v3.0)

隐私保护的数据导出，支持ML兼容格式和统计摘要。
"""
import json
import csv
import io
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np

from ..privacy.dp.mechanisms import LaplaceMechanism


class ExportFormat(Enum):
    """导出格式"""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    NUMPY = "numpy"


@dataclass
class ExportConfig:
    """导出配置"""
    format: ExportFormat = ExportFormat.CSV
    epsilon: float = 1.0
    add_noise_to_numeric: bool = True
    mask_identifiers: bool = True
    include_statistics: bool = True
    max_rows: Optional[int] = None


@dataclass
class StatisticalSummary:
    """统计摘要"""
    column_name: str
    data_type: str
    count: int
    null_count: int
    mean: Optional[float] = None
    std: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unique_count: Optional[int] = None
    is_noisy: bool = False
    epsilon_used: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "column_name": self.column_name,
            "data_type": self.data_type,
            "count": self.count,
            "null_count": self.null_count,
            "mean": self.mean,
            "std": self.std,
            "min": self.min_value,
            "max": self.max_value,
            "unique_count": self.unique_count,
            "is_noisy": self.is_noisy,
            "epsilon_used": self.epsilon_used,
        }


class PrivacyPreservingExporter:
    """
    隐私保护数据导出器
    
    提供:
    - ML兼容的导出格式
    - 差分隐私统计摘要
    - 标识符脱敏
    - 数值噪声添加
    """
    
    def __init__(self, default_epsilon: float = 1.0):
        """
        初始化导出器
        
        Args:
            default_epsilon: 默认epsilon值
        """
        self.default_epsilon = default_epsilon
        self._laplace = LaplaceMechanism(epsilon=default_epsilon)
    
    def export_data(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig = None,
        identifier_columns: List[str] = None,
    ) -> str:
        """
        导出数据
        
        Args:
            data: 数据列表
            config: 导出配置
            identifier_columns: 标识符列
            
        Returns:
            导出的数据字符串
        """
        config = config or ExportConfig()
        identifier_columns = identifier_columns or []
        
        # 限制行数
        if config.max_rows and len(data) > config.max_rows:
            data = data[:config.max_rows]
        
        # 处理数据
        processed_data = self._process_data(data, config, identifier_columns)
        
        # 根据格式导出
        if config.format == ExportFormat.CSV:
            return self._export_csv(processed_data)
        elif config.format == ExportFormat.JSON:
            return self._export_json(processed_data)
        else:
            return self._export_json(processed_data)
    
    def _process_data(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
        identifier_columns: List[str],
    ) -> List[Dict[str, Any]]:
        """处理数据"""
        processed = []
        
        for row in data:
            new_row = {}
            for key, value in row.items():
                # 脱敏标识符
                if config.mask_identifiers and key.lower() in [c.lower() for c in identifier_columns]:
                    new_row[key] = self._mask_identifier(value)
                # 添加噪声到数值
                elif config.add_noise_to_numeric and isinstance(value, (int, float)):
                    new_row[key] = self._add_noise(value, config.epsilon)
                else:
                    new_row[key] = value
            processed.append(new_row)
        
        return processed
    
    def _mask_identifier(self, value: Any) -> str:
        """脱敏标识符"""
        if value is None:
            return None
        
        str_value = str(value)
        if len(str_value) <= 2:
            return "*" * len(str_value)
        
        return str_value[0] + "*" * (len(str_value) - 2) + str_value[-1]
    
    def _add_noise(self, value: float, epsilon: float) -> float:
        """添加噪声"""
        laplace = LaplaceMechanism(epsilon=epsilon, sensitivity=1.0)
        return laplace.add_noise(value)
    
    def _export_csv(self, data: List[Dict[str, Any]]) -> str:
        """导出为CSV"""
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    def _export_json(self, data: List[Dict[str, Any]]) -> str:
        """导出为JSON"""
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    def compute_statistics(
        self,
        data: List[Dict[str, Any]],
        epsilon: float = None,
        columns: List[str] = None,
    ) -> List[StatisticalSummary]:
        """
        计算差分隐私统计摘要
        
        Args:
            data: 数据列表
            epsilon: epsilon值
            columns: 要计算的列
            
        Returns:
            统计摘要列表
        """
        epsilon = epsilon or self.default_epsilon
        
        if not data:
            return []
        
        # 确定要计算的列
        if columns is None:
            columns = list(data[0].keys())
        
        summaries = []
        
        for col in columns:
            values = [row.get(col) for row in data]
            summary = self._compute_column_statistics(col, values, epsilon)
            summaries.append(summary)
        
        return summaries
    
    def _compute_column_statistics(
        self,
        column_name: str,
        values: List[Any],
        epsilon: float,
    ) -> StatisticalSummary:
        """计算单列统计"""
        # 基本统计
        count = len(values)
        null_count = sum(1 for v in values if v is None)
        non_null_values = [v for v in values if v is not None]
        
        # 确定数据类型
        numeric_values = []
        for v in non_null_values:
            if isinstance(v, (int, float)):
                numeric_values.append(float(v))
        
        is_numeric = len(numeric_values) > len(non_null_values) * 0.5
        
        summary = StatisticalSummary(
            column_name=column_name,
            data_type="numeric" if is_numeric else "categorical",
            count=count,
            null_count=null_count,
        )
        
        if is_numeric and numeric_values:
            # 计算带噪声的统计量
            laplace = LaplaceMechanism(epsilon=epsilon / 4, sensitivity=1.0)  # 分配epsilon
            
            summary.mean = laplace.add_noise(np.mean(numeric_values))
            summary.std = max(0, laplace.add_noise(np.std(numeric_values)))
            summary.min_value = laplace.add_noise(min(numeric_values))
            summary.max_value = laplace.add_noise(max(numeric_values))
            summary.is_noisy = True
            summary.epsilon_used = epsilon
        else:
            # 分类数据
            summary.unique_count = len(set(non_null_values))
        
        return summary
    
    def export_for_ml(
        self,
        data: List[Dict[str, Any]],
        target_column: str,
        feature_columns: List[str] = None,
        epsilon: float = None,
    ) -> Dict[str, Any]:
        """
        导出为ML训练格式
        
        Args:
            data: 数据列表
            target_column: 目标列
            feature_columns: 特征列
            epsilon: epsilon值
            
        Returns:
            包含features和target的字典
        """
        epsilon = epsilon or self.default_epsilon
        
        if not data:
            return {"features": [], "target": [], "feature_names": []}
        
        if feature_columns is None:
            feature_columns = [k for k in data[0].keys() if k != target_column]
        
        features = []
        target = []
        
        laplace = LaplaceMechanism(epsilon=epsilon, sensitivity=1.0)
        
        for row in data:
            # 提取特征
            feature_row = []
            for col in feature_columns:
                value = row.get(col, 0)
                if isinstance(value, (int, float)):
                    # 添加噪声
                    value = laplace.add_noise(float(value))
                else:
                    value = 0  # 非数值转为0
                feature_row.append(value)
            
            features.append(feature_row)
            
            # 提取目标
            target_value = row.get(target_column, 0)
            if isinstance(target_value, (int, float)):
                target_value = laplace.add_noise(float(target_value))
            target.append(target_value)
        
        return {
            "features": features,
            "target": target,
            "feature_names": feature_columns,
            "epsilon_used": epsilon,
        }
