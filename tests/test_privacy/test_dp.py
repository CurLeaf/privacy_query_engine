"""
差分隐私模块单元测试
"""
import pytest
import numpy as np
from main.privacy.dp import (
    LaplaceMechanism, 
    GaussianMechanism,
    add_laplace_noise,
    DPRewriter,
)


class TestLaplaceMechanism:
    """拉普拉斯机制测试"""
    
    def test_add_noise(self):
        """测试噪声添加"""
        mech = LaplaceMechanism(epsilon=1.0, sensitivity=1.0)
        original = 100
        noised = mech.add_noise(original)
        
        # 噪声值应该不同于原始值 (极小概率相等)
        assert isinstance(noised, float)
    
    def test_noise_distribution(self):
        """测试噪声分布 (大数定律)"""
        mech = LaplaceMechanism(epsilon=1.0, sensitivity=1.0)
        original = 1000
        
        # 多次采样取平均
        samples = [mech.add_noise(original) for _ in range(10000)]
        mean_noised = np.mean(samples)
        
        # 期望值应接近原始值
        assert abs(mean_noised - original) < 50  # 容忍误差
    
    def test_epsilon_effect(self):
        """测试epsilon对噪声的影响"""
        # epsilon越大，噪声越小
        np.random.seed(42)
        mech_high_eps = LaplaceMechanism(epsilon=10.0)
        np.random.seed(42)
        mech_low_eps = LaplaceMechanism(epsilon=0.1)
        
        # 高epsilon的scale更小
        assert mech_high_eps.scale < mech_low_eps.scale


class TestDPRewriter:
    """DP重写器测试"""
    
    def setup_method(self):
        self.rewriter = DPRewriter(default_epsilon=1.0)
    
    def test_apply_dp_to_number(self):
        """测试对单个数值应用DP"""
        result = self.rewriter.apply_dp(1000)
        assert isinstance(result, float)
    
    def test_apply_dp_to_dict(self):
        """测试对字典应用DP"""
        original = {"count": 100, "sum": 5000}
        result = self.rewriter.apply_dp(original)
        
        assert isinstance(result, dict)
        assert "count" in result
        assert "sum" in result
    
    def test_create_privacy_info(self):
        """测试隐私信息生成"""
        info = self.rewriter.create_privacy_info(
            epsilon=1.0,
            sensitivity=1.0,
            mechanism="laplace"
        )
        
        assert info["epsilon"] == 1.0
        assert info["method"] == "Laplace"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

