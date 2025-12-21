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



class TestExponentialMechanism:
    """指数机制测试"""
    
    def test_select_from_candidates(self):
        """测试从候选集中选择"""
        from main.privacy.dp import ExponentialMechanism
        
        mechanism = ExponentialMechanism(epsilon=1.0)
        candidates = ["A", "B", "C", "D"]
        utility_scores = [1.0, 2.0, 3.0, 4.0]
        
        selected, idx = mechanism.select(candidates, utility_scores)
        
        assert selected in candidates
        assert 0 <= idx < len(candidates)
    
    def test_higher_utility_more_likely(self):
        """测试高效用值更可能被选中"""
        from main.privacy.dp import ExponentialMechanism
        
        mechanism = ExponentialMechanism(epsilon=10.0)  # 高epsilon使选择更确定
        candidates = ["low", "high"]
        utility_scores = [0.0, 100.0]
        
        # 多次选择，高效用应该更常被选中
        high_count = 0
        for _ in range(100):
            selected, _ = mechanism.select(candidates, utility_scores)
            if selected == "high":
                high_count += 1
        
        assert high_count > 50  # 高效用应该被选中超过一半


class TestSparseVectorTechnique:
    """稀疏向量技术测试"""
    
    def test_above_threshold(self):
        """测试高于阈值的查询"""
        from main.privacy.dp import SparseVectorTechnique
        
        svt = SparseVectorTechnique(
            epsilon=1.0,
            threshold=50.0,
            max_above_threshold=3
        )
        
        # 测试明显高于阈值的值
        result = svt.query(100.0)
        # 由于噪声，结果可能不确定，但应该是布尔值
        assert isinstance(result, bool)
    
    def test_max_above_threshold_limit(self):
        """测试最大高于阈值数量限制"""
        from main.privacy.dp import SparseVectorTechnique
        
        svt = SparseVectorTechnique(
            epsilon=10.0,  # 高epsilon减少噪声
            threshold=0.0,
            max_above_threshold=2
        )
        
        # 查询多个明显高于阈值的值
        results = []
        for _ in range(10):
            results.append(svt.query(1000.0))
        
        # 最多只有2个True
        assert sum(results) <= 2
    
    def test_batch_query(self):
        """测试批量查询"""
        from main.privacy.dp import SparseVectorTechnique
        
        svt = SparseVectorTechnique(
            epsilon=1.0,
            threshold=50.0,
            max_above_threshold=2
        )
        
        values = [10.0, 60.0, 70.0, 80.0, 90.0]
        results = svt.batch_query(values)
        
        assert len(results) == len(values)
        assert all(isinstance(r, bool) for r in results)
