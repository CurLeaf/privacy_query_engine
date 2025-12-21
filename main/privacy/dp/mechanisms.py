"""
Differential Privacy Mechanisms - 差分隐私噪声机制
支持 Laplace 和 Gaussian 机制
"""
import numpy as np
from typing import Union


def add_laplace_noise(
    value: Union[int, float],
    epsilon: float,
    sensitivity: float = 1.0
) -> float:
    """
    添加拉普拉斯噪声
    
    Args:
        value: 原始值
        epsilon: 隐私预算参数
        sensitivity: 查询敏感度
        
    Returns:
        加噪后的值
    """
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return value + noise


def add_gaussian_noise(
    value: Union[int, float],
    epsilon: float,
    delta: float,
    sensitivity: float = 1.0
) -> float:
    """
    添加高斯噪声 (用于 (ε,δ)-差分隐私)
    
    Args:
        value: 原始值
        epsilon: 隐私预算参数
        delta: 隐私失败概率
        sensitivity: 查询敏感度
        
    Returns:
        加噪后的值
    """
    sigma = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
    noise = np.random.normal(0, sigma)
    return value + noise


class LaplaceMechanism:
    """拉普拉斯机制"""
    
    def __init__(self, epsilon: float, sensitivity: float = 1.0):
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.scale = sensitivity / epsilon
    
    def add_noise(self, value: Union[int, float]) -> float:
        """添加噪声"""
        return add_laplace_noise(value, self.epsilon, self.sensitivity)
    
    def __repr__(self):
        return f"LaplaceMechanism(epsilon={self.epsilon}, sensitivity={self.sensitivity})"


class GaussianMechanism:
    """高斯机制"""
    
    def __init__(self, epsilon: float, delta: float, sensitivity: float = 1.0):
        self.epsilon = epsilon
        self.delta = delta
        self.sensitivity = sensitivity
        self.sigma = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
    
    def add_noise(self, value: Union[int, float]) -> float:
        """添加噪声"""
        return add_gaussian_noise(value, self.epsilon, self.delta, self.sensitivity)
    
    def __repr__(self):
        return f"GaussianMechanism(epsilon={self.epsilon}, delta={self.delta}, sensitivity={self.sensitivity})"


class ExponentialMechanism:
    """
    指数机制 - 用于从候选集中选择最优项
    适用于分类数据和非数值查询
    """
    
    def __init__(self, epsilon: float, sensitivity: float = 1.0):
        """
        初始化指数机制
        
        Args:
            epsilon: 隐私预算参数
            sensitivity: 效用函数的敏感度
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
    
    def select(
        self,
        candidates: list,
        utility_scores: list
    ) -> tuple:
        """
        从候选集中选择一个元素
        
        Args:
            candidates: 候选元素列表
            utility_scores: 每个候选元素的效用分数
            
        Returns:
            (选中的元素, 选中元素的索引)
        """
        if len(candidates) != len(utility_scores):
            raise ValueError("candidates and utility_scores must have the same length")
        
        if len(candidates) == 0:
            raise ValueError("candidates cannot be empty")
        
        # 计算每个候选的选择概率
        scores = np.array(utility_scores, dtype=float)
        
        # 指数机制概率: P(r) ∝ exp(ε * u(r) / (2 * Δu))
        exponents = (self.epsilon * scores) / (2 * self.sensitivity)
        
        # 数值稳定性处理
        exponents = exponents - np.max(exponents)
        probabilities = np.exp(exponents)
        probabilities = probabilities / np.sum(probabilities)
        
        # 根据概率选择
        selected_idx = np.random.choice(len(candidates), p=probabilities)
        
        return candidates[selected_idx], selected_idx
    
    def __repr__(self):
        return f"ExponentialMechanism(epsilon={self.epsilon}, sensitivity={self.sensitivity})"


class SparseVectorTechnique:
    """
    稀疏向量技术 (SVT) - 用于阈值查询
    在达到指定数量的"高于阈值"响应后停止
    """
    
    def __init__(
        self,
        epsilon: float,
        threshold: float,
        max_above_threshold: int = 1,
        sensitivity: float = 1.0
    ):
        """
        初始化稀疏向量技术
        
        Args:
            epsilon: 总隐私预算
            threshold: 阈值
            max_above_threshold: 最多返回多少个"高于阈值"的结果
            sensitivity: 查询敏感度
        """
        self.epsilon = epsilon
        self.threshold = threshold
        self.max_above_threshold = max_above_threshold
        self.sensitivity = sensitivity
        
        # 分配预算: 一半给阈值噪声，一半给查询噪声
        self.epsilon_threshold = epsilon / 2
        self.epsilon_query = epsilon / 2
        
        # 添加噪声到阈值
        self.noisy_threshold = threshold + np.random.laplace(
            0, 2 * sensitivity / self.epsilon_threshold
        )
        
        self.above_count = 0
    
    def query(self, value: float) -> bool:
        """
        查询一个值是否高于阈值
        
        Args:
            value: 查询值
            
        Returns:
            True 如果值高于噪声阈值，False 否则
        """
        if self.above_count >= self.max_above_threshold:
            return False
        
        # 添加噪声到查询值
        noisy_value = value + np.random.laplace(
            0, 4 * self.max_above_threshold * self.sensitivity / self.epsilon_query
        )
        
        if noisy_value >= self.noisy_threshold:
            self.above_count += 1
            return True
        
        return False
    
    def batch_query(self, values: list) -> list:
        """
        批量查询多个值
        
        Args:
            values: 查询值列表
            
        Returns:
            布尔值列表，表示每个值是否高于阈值
        """
        results = []
        for value in values:
            if self.above_count >= self.max_above_threshold:
                results.append(False)
            else:
                results.append(self.query(value))
        return results
    
    def reset(self):
        """重置计数器和阈值噪声"""
        self.noisy_threshold = self.threshold + np.random.laplace(
            0, 2 * self.sensitivity / self.epsilon_threshold
        )
        self.above_count = 0
    
    def __repr__(self):
        return f"SparseVectorTechnique(epsilon={self.epsilon}, threshold={self.threshold}, max_above={self.max_above_threshold})"

