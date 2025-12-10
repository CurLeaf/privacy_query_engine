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

