"""
Tests for Advanced Analytics (v3.0)
"""
import pytest

from main.analytics import (
    PrivacyPreservingExporter,
    ExportFormat,
    FederatedLearningAggregator,
    SyntheticDataGenerator,
)
from main.analytics.export import ExportConfig
from main.analytics.federated import ModelUpdate
from main.analytics.synthetic import SyntheticDataConfig


class TestPrivacyPreservingExporter:
    """隐私保护导出器测试"""
    
    def setup_method(self):
        self.exporter = PrivacyPreservingExporter()
        self.test_data = [
            {"id": 1, "name": "Alice", "age": 30, "salary": 50000},
            {"id": 2, "name": "Bob", "age": 25, "salary": 45000},
            {"id": 3, "name": "Charlie", "age": 35, "salary": 60000},
        ]
    
    def test_export_csv(self):
        """测试CSV导出"""
        config = ExportConfig(format=ExportFormat.CSV, add_noise_to_numeric=False)
        result = self.exporter.export_data(self.test_data, config)
        
        assert "id" in result
        assert "name" in result
        assert "age" in result
    
    def test_export_json(self):
        """测试JSON导出"""
        config = ExportConfig(format=ExportFormat.JSON, add_noise_to_numeric=False)
        result = self.exporter.export_data(self.test_data, config)
        
        assert "Alice" in result
        assert "Bob" in result
    
    def test_mask_identifiers(self):
        """测试标识符脱敏"""
        config = ExportConfig(mask_identifiers=True, add_noise_to_numeric=False)
        result = self.exporter.export_data(
            self.test_data, 
            config, 
            identifier_columns=["name"]
        )
        
        # 名字应该被脱敏
        assert "Alice" not in result
        assert "A***e" in result or "A**e" in result
    
    def test_add_noise_to_numeric(self):
        """测试数值噪声"""
        config = ExportConfig(add_noise_to_numeric=True, epsilon=0.1)
        result = self.exporter.export_data(self.test_data, config)
        
        # 结果应该包含数据但值可能不同
        assert "age" in result or "salary" in result
    
    def test_compute_statistics(self):
        """测试统计计算"""
        stats = self.exporter.compute_statistics(self.test_data, epsilon=1.0)
        
        assert len(stats) > 0
        
        # 找到age列的统计
        age_stat = next((s for s in stats if s.column_name == "age"), None)
        assert age_stat is not None
        assert age_stat.data_type == "numeric"
        assert age_stat.mean is not None
    
    def test_export_for_ml(self):
        """测试ML格式导出"""
        result = self.exporter.export_for_ml(
            self.test_data,
            target_column="salary",
            feature_columns=["age"],
        )
        
        assert "features" in result
        assert "target" in result
        assert len(result["features"]) == 3


class TestFederatedLearningAggregator:
    """联邦学习聚合器测试"""
    
    def setup_method(self):
        self.aggregator = FederatedLearningAggregator(epsilon=1.0)
    
    def test_aggregate_updates(self):
        """测试模型更新聚合"""
        updates = [
            ModelUpdate("client1", [1.0, 2.0, 3.0], 100),
            ModelUpdate("client2", [1.5, 2.5, 3.5], 100),
            ModelUpdate("client3", [0.5, 1.5, 2.5], 100),
        ]
        
        result = self.aggregator.aggregate_updates(updates)
        
        assert result.num_clients == 3
        assert result.total_samples == 300
        assert len(result.weights) == 3
    
    def test_aggregate_with_different_samples(self):
        """测试不同样本数的聚合"""
        updates = [
            ModelUpdate("client1", [1.0, 2.0], 100),
            ModelUpdate("client2", [2.0, 4.0], 300),  # 更多样本
        ]
        
        result = self.aggregator.aggregate_updates(updates)
        
        # client2应该有更大的权重
        assert result.total_samples == 400
    
    def test_secure_average(self):
        """测试安全平均"""
        values = [10.0, 20.0, 30.0]
        
        result = self.aggregator.secure_average(values)
        
        # 结果应该接近20但有噪声
        assert 0 < result < 50
    
    def test_evaluate_model_private(self):
        """测试隐私保护模型评估"""
        predictions = [1.0, 2.0, 3.0, 4.0, 5.0]
        labels = [1.1, 2.1, 2.9, 4.0, 5.1]
        
        result = self.aggregator.evaluate_model_private(predictions, labels)
        
        assert "mse" in result
        assert "mae" in result
        assert "accuracy" in result
        assert result["mse"] >= 0
    
    def test_compute_gradient_private(self):
        """测试隐私保护梯度计算"""
        gradients = [
            [0.1, 0.2, 0.3],
            [0.15, 0.25, 0.35],
            [0.05, 0.15, 0.25],
        ]
        
        result = self.aggregator.compute_gradient_private(gradients)
        
        assert len(result) == 3


class TestSyntheticDataGenerator:
    """合成数据生成器测试"""
    
    def setup_method(self):
        self.generator = SyntheticDataGenerator(epsilon=1.0)
        self.test_data = [
            {"age": 30, "income": 50000, "city": "NYC"},
            {"age": 25, "income": 45000, "city": "LA"},
            {"age": 35, "income": 60000, "city": "NYC"},
            {"age": 28, "income": 52000, "city": "Chicago"},
            {"age": 40, "income": 70000, "city": "LA"},
        ]
    
    def test_learn_schema(self):
        """测试模式学习"""
        schemas = self.generator.learn_schema(self.test_data)
        
        assert len(schemas) == 3
        
        age_schema = next((s for s in schemas if s.name == "age"), None)
        assert age_schema is not None
        assert age_schema.data_type == "numeric"
        
        city_schema = next((s for s in schemas if s.name == "city"), None)
        assert city_schema is not None
        assert city_schema.data_type == "categorical"
    
    def test_generate_from_schema(self):
        """测试从模式生成"""
        schemas = self.generator.learn_schema(self.test_data)
        config = SyntheticDataConfig(num_rows=10, seed=42)
        
        synthetic = self.generator.generate(schemas, config)
        
        assert len(synthetic) == 10
        assert "age" in synthetic[0]
        assert "income" in synthetic[0]
        assert "city" in synthetic[0]
    
    def test_generate_from_data(self):
        """测试从数据直接生成"""
        config = SyntheticDataConfig(num_rows=5, seed=42)
        
        synthetic = self.generator.generate_from_data(self.test_data, config)
        
        assert len(synthetic) == 5
    
    def test_compute_utility_metrics(self):
        """测试效用指标计算"""
        config = SyntheticDataConfig(num_rows=100, seed=42)
        synthetic = self.generator.generate_from_data(self.test_data, config)
        
        metrics = self.generator.compute_utility_metrics(self.test_data, synthetic)
        
        assert "num_original" in metrics
        assert "num_synthetic" in metrics
        assert "column_metrics" in metrics
        assert "age" in metrics["column_metrics"]
