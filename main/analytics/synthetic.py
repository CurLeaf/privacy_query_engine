"""
Synthetic Data Generation (v3.0)

差分隐私合成数据生成。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import random

from ..privacy.dp.mechanisms import LaplaceMechanism


@dataclass
class ColumnSchema:
    """列模式"""
    name: str
    data_type: str  # "numeric", "categorical", "datetime"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    categories: Optional[List[str]] = None
    mean: Optional[float] = None
    std: Optional[float] = None


@dataclass
class SyntheticDataConfig:
    """合成数据配置"""
    num_rows: int = 1000
    epsilon: float = 1.0
    preserve_correlations: bool = True
    seed: Optional[int] = None


class SyntheticDataGenerator:
    """
    合成数据生成器
    
    提供:
    - 差分隐私合成数据生成
    - 数据效用保持
    - 多种数据类型支持
    """
    
    def __init__(self, epsilon: float = 1.0):
        """
        初始化生成器
        
        Args:
            epsilon: 差分隐私epsilon
        """
        self.epsilon = epsilon
        self._laplace = LaplaceMechanism(epsilon=epsilon)
    
    def learn_schema(
        self,
        data: List[Dict[str, Any]],
        epsilon: float = None,
    ) -> List[ColumnSchema]:
        """
        从数据学习模式
        
        Args:
            data: 原始数据
            epsilon: epsilon值
            
        Returns:
            列模式列表
        """
        if not data:
            return []
        
        epsilon = epsilon or self.epsilon
        laplace = LaplaceMechanism(epsilon=epsilon / len(data[0]), sensitivity=1.0)
        
        schemas = []
        
        for col in data[0].keys():
            values = [row.get(col) for row in data if row.get(col) is not None]
            
            if not values:
                continue
            
            # 判断数据类型
            numeric_values = []
            for v in values:
                if isinstance(v, (int, float)):
                    numeric_values.append(float(v))
            
            if len(numeric_values) > len(values) * 0.5:
                # 数值类型
                schema = ColumnSchema(
                    name=col,
                    data_type="numeric",
                    min_value=laplace.add_noise(min(numeric_values)),
                    max_value=laplace.add_noise(max(numeric_values)),
                    mean=laplace.add_noise(np.mean(numeric_values)),
                    std=max(0.1, laplace.add_noise(np.std(numeric_values))),
                )
            else:
                # 分类类型
                categories = list(set(str(v) for v in values))
                schema = ColumnSchema(
                    name=col,
                    data_type="categorical",
                    categories=categories[:100],  # 限制类别数
                )
            
            schemas.append(schema)
        
        return schemas
    
    def generate(
        self,
        schemas: List[ColumnSchema],
        config: SyntheticDataConfig = None,
    ) -> List[Dict[str, Any]]:
        """
        生成合成数据
        
        Args:
            schemas: 列模式
            config: 生成配置
            
        Returns:
            合成数据列表
        """
        config = config or SyntheticDataConfig()
        
        if config.seed is not None:
            np.random.seed(config.seed)
            random.seed(config.seed)
        
        synthetic_data = []
        
        for _ in range(config.num_rows):
            row = {}
            for schema in schemas:
                row[schema.name] = self._generate_value(schema, config.epsilon)
            synthetic_data.append(row)
        
        return synthetic_data
    
    def _generate_value(self, schema: ColumnSchema, epsilon: float) -> Any:
        """生成单个值"""
        if schema.data_type == "numeric":
            return self._generate_numeric(schema, epsilon)
        elif schema.data_type == "categorical":
            return self._generate_categorical(schema)
        else:
            return None
    
    def _generate_numeric(self, schema: ColumnSchema, epsilon: float) -> float:
        """生成数值"""
        if schema.mean is not None and schema.std is not None:
            # 使用正态分布
            value = np.random.normal(schema.mean, schema.std)
        else:
            # 使用均匀分布
            min_val = schema.min_value or 0
            max_val = schema.max_value or 100
            value = np.random.uniform(min_val, max_val)
        
        # 裁剪到范围内
        if schema.min_value is not None:
            value = max(schema.min_value, value)
        if schema.max_value is not None:
            value = min(schema.max_value, value)
        
        return round(value, 2)
    
    def _generate_categorical(self, schema: ColumnSchema) -> str:
        """生成分类值"""
        if not schema.categories:
            return "unknown"
        return random.choice(schema.categories)
    
    def generate_from_data(
        self,
        original_data: List[Dict[str, Any]],
        config: SyntheticDataConfig = None,
    ) -> List[Dict[str, Any]]:
        """
        从原始数据生成合成数据
        
        Args:
            original_data: 原始数据
            config: 生成配置
            
        Returns:
            合成数据列表
        """
        config = config or SyntheticDataConfig()
        
        # 学习模式
        schemas = self.learn_schema(original_data, config.epsilon / 2)
        
        # 生成数据
        return self.generate(schemas, config)
    
    def compute_utility_metrics(
        self,
        original_data: List[Dict[str, Any]],
        synthetic_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        计算数据效用指标
        
        Args:
            original_data: 原始数据
            synthetic_data: 合成数据
            
        Returns:
            效用指标
        """
        if not original_data or not synthetic_data:
            return {"error": "Empty data"}
        
        metrics = {
            "num_original": len(original_data),
            "num_synthetic": len(synthetic_data),
            "column_metrics": {},
        }
        
        for col in original_data[0].keys():
            orig_values = [row.get(col) for row in original_data if row.get(col) is not None]
            synth_values = [row.get(col) for row in synthetic_data if row.get(col) is not None]
            
            if not orig_values or not synth_values:
                continue
            
            # 检查是否为数值
            orig_numeric = [v for v in orig_values if isinstance(v, (int, float))]
            synth_numeric = [v for v in synth_values if isinstance(v, (int, float))]
            
            if len(orig_numeric) > len(orig_values) * 0.5:
                # 数值列
                orig_mean = np.mean(orig_numeric)
                synth_mean = np.mean(synth_numeric)
                orig_std = np.std(orig_numeric)
                synth_std = np.std(synth_numeric)
                
                metrics["column_metrics"][col] = {
                    "type": "numeric",
                    "mean_diff": abs(orig_mean - synth_mean),
                    "std_diff": abs(orig_std - synth_std),
                    "mean_relative_error": abs(orig_mean - synth_mean) / (abs(orig_mean) + 1e-10),
                }
            else:
                # 分类列
                orig_unique = set(str(v) for v in orig_values)
                synth_unique = set(str(v) for v in synth_values)
                
                metrics["column_metrics"][col] = {
                    "type": "categorical",
                    "orig_categories": len(orig_unique),
                    "synth_categories": len(synth_unique),
                    "category_overlap": len(orig_unique & synth_unique) / len(orig_unique) if orig_unique else 0,
                }
        
        return metrics
