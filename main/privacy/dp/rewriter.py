"""
DPRewriter - 差分隐私重写器
职责: 对聚合查询结果添加噪声
"""
from typing import Any, Dict, Union

from .mechanisms import LaplaceMechanism, GaussianMechanism
from .sensitivity import SensitivityAnalyzer


class DPRewriter:
    """差分隐私重写器"""
    
    def __init__(self, default_epsilon: float = 1.0, default_sensitivity: float = 1.0):
        self.default_epsilon = default_epsilon
        self.default_sensitivity = default_sensitivity
        self.sensitivity_analyzer = SensitivityAnalyzer()
    
    def apply_dp(
        self,
        result: Union[int, float, Dict[str, Any]],
        epsilon: float = None,
        sensitivity: float = None,
        mechanism: str = "laplace"
    ) -> Union[float, Dict[str, Any]]:
        """
        对查询结果应用差分隐私保护
        
        Args:
            result: 原始查询结果 (数值或字典)
            epsilon: 隐私预算参数
            sensitivity: 查询敏感度
            mechanism: 噪声机制 ("laplace" 或 "gaussian")
            
        Returns:
            加噪后的结果
        """
        epsilon = epsilon or self.default_epsilon
        sensitivity = sensitivity or self.default_sensitivity
        
        if mechanism == "laplace":
            mech = LaplaceMechanism(epsilon, sensitivity)
        elif mechanism == "gaussian":
            mech = GaussianMechanism(epsilon, delta=1e-5, sensitivity=sensitivity)
        else:
            raise ValueError(f"Unsupported mechanism: {mechanism}")
        
        # 处理单个数值
        if isinstance(result, (int, float)):
            return mech.add_noise(result)
        
        # 处理字典结果 (多个聚合值)
        if isinstance(result, dict):
            noised_result = {}
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    noised_result[key] = mech.add_noise(value)
                else:
                    noised_result[key] = value
            return noised_result
        
        return result
    
    def create_privacy_info(
        self,
        epsilon: float,
        sensitivity: float,
        mechanism: str
    ) -> Dict[str, Any]:
        """生成隐私信息元数据"""
        return {
            "epsilon": epsilon,
            "sensitivity": sensitivity,
            "method": mechanism.capitalize(),
        }

