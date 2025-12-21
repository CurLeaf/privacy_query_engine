"""
Federated Learning Support (v3.0)

联邦学习支持，提供隐私保护的模型聚合和评估。
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from ..privacy.dp.mechanisms import LaplaceMechanism


@dataclass
class ModelUpdate:
    """模型更新"""
    client_id: str
    weights: List[float]
    num_samples: int
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedModel:
    """聚合后的模型"""
    weights: List[float]
    num_clients: int
    total_samples: int
    epsilon_used: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": self.weights,
            "num_clients": self.num_clients,
            "total_samples": self.total_samples,
            "epsilon_used": self.epsilon_used,
            "timestamp": self.timestamp.isoformat(),
        }


class FederatedLearningAggregator:
    """
    联邦学习聚合器
    
    提供:
    - 差分隐私模型聚合
    - 安全平均
    - 隐私保护模型评估
    """
    
    def __init__(self, epsilon: float = 1.0, clip_norm: float = 1.0):
        """
        初始化聚合器
        
        Args:
            epsilon: 差分隐私epsilon
            clip_norm: 梯度裁剪范数
        """
        self.epsilon = epsilon
        self.clip_norm = clip_norm
        self._laplace = LaplaceMechanism(epsilon=epsilon)
    
    def aggregate_updates(
        self,
        updates: List[ModelUpdate],
        add_noise: bool = True,
    ) -> AggregatedModel:
        """
        聚合模型更新
        
        Args:
            updates: 模型更新列表
            add_noise: 是否添加噪声
            
        Returns:
            聚合后的模型
        """
        if not updates:
            return AggregatedModel(
                weights=[],
                num_clients=0,
                total_samples=0,
                epsilon_used=0,
            )
        
        # 裁剪权重
        clipped_updates = [self._clip_weights(u.weights) for u in updates]
        
        # 计算加权平均
        total_samples = sum(u.num_samples for u in updates)
        
        if total_samples == 0:
            total_samples = len(updates)
            sample_weights = [1.0 / len(updates)] * len(updates)
        else:
            sample_weights = [u.num_samples / total_samples for u in updates]
        
        # 聚合
        num_weights = len(clipped_updates[0])
        aggregated_weights = []
        
        for i in range(num_weights):
            weighted_sum = sum(
                clipped_updates[j][i] * sample_weights[j]
                for j in range(len(updates))
            )
            
            # 添加噪声
            if add_noise:
                noise_laplace = LaplaceMechanism(
                    epsilon=self.epsilon,
                    sensitivity=self.clip_norm / total_samples,
                )
                weighted_sum = noise_laplace.add_noise(weighted_sum)
            
            aggregated_weights.append(weighted_sum)
        
        return AggregatedModel(
            weights=aggregated_weights,
            num_clients=len(updates),
            total_samples=total_samples,
            epsilon_used=self.epsilon if add_noise else 0,
        )
    
    def _clip_weights(self, weights: List[float]) -> List[float]:
        """裁剪权重"""
        weights_array = np.array(weights)
        norm = np.linalg.norm(weights_array)
        
        if norm > self.clip_norm:
            weights_array = weights_array * (self.clip_norm / norm)
        
        return weights_array.tolist()
    
    def secure_average(
        self,
        values: List[float],
        epsilon: float = None,
    ) -> float:
        """
        安全平均
        
        Args:
            values: 值列表
            epsilon: epsilon值
            
        Returns:
            带噪声的平均值
        """
        if not values:
            return 0.0
        
        epsilon = epsilon or self.epsilon
        laplace = LaplaceMechanism(epsilon=epsilon, sensitivity=1.0 / len(values))
        
        avg = sum(values) / len(values)
        return laplace.add_noise(avg)
    
    def evaluate_model_private(
        self,
        predictions: List[float],
        labels: List[float],
        epsilon: float = None,
    ) -> Dict[str, float]:
        """
        隐私保护模型评估
        
        Args:
            predictions: 预测值
            labels: 真实标签
            epsilon: epsilon值
            
        Returns:
            评估指标
        """
        if not predictions or len(predictions) != len(labels):
            return {"error": "Invalid input"}
        
        epsilon = epsilon or self.epsilon
        n = len(predictions)
        laplace = LaplaceMechanism(epsilon=epsilon / 3, sensitivity=1.0 / n)  # 分配给3个指标
        
        # 计算MSE
        mse = sum((p - l) ** 2 for p, l in zip(predictions, labels)) / n
        noisy_mse = max(0, laplace.add_noise(mse))
        
        # 计算MAE
        mae = sum(abs(p - l) for p, l in zip(predictions, labels)) / n
        noisy_mae = max(0, laplace.add_noise(mae))
        
        # 计算准确率 (用于分类)
        accuracy = sum(1 for p, l in zip(predictions, labels) if round(p) == round(l)) / n
        noisy_accuracy = min(1.0, max(0, laplace.add_noise(accuracy)))
        
        return {
            "mse": noisy_mse,
            "mae": noisy_mae,
            "accuracy": noisy_accuracy,
            "epsilon_used": epsilon,
            "num_samples": n,
        }
    
    def compute_gradient_private(
        self,
        gradients: List[List[float]],
        epsilon: float = None,
    ) -> List[float]:
        """
        计算隐私保护梯度
        
        Args:
            gradients: 梯度列表
            epsilon: epsilon值
            
        Returns:
            聚合后的梯度
        """
        if not gradients:
            return []
        
        epsilon = epsilon or self.epsilon
        
        # 裁剪梯度
        clipped = [self._clip_weights(g) for g in gradients]
        
        laplace = LaplaceMechanism(epsilon=epsilon, sensitivity=self.clip_norm / len(clipped))
        
        # 聚合
        num_dims = len(clipped[0])
        aggregated = []
        
        for i in range(num_dims):
            avg = sum(g[i] for g in clipped) / len(clipped)
            noisy_avg = laplace.add_noise(avg)
            aggregated.append(noisy_avg)
        
        return aggregated
