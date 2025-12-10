"""
去标识化模块单元测试
"""
import pytest
from main.privacy.deid import (
    DeIDRewriter,
    hash_value,
    mask_email,
    mask_phone,
    mask_name,
    generalize_age,
)


class TestDeIDMethods:
    """去标识化方法测试"""
    
    def test_hash_value(self):
        """测试哈希方法"""
        result = hash_value("secret_data")
        
        assert isinstance(result, str)
        assert len(result) == 16  # 默认长度
        
        # 相同输入应产生相同输出
        assert hash_value("test") == hash_value("test")
        
        # 不同输入应产生不同输出
        assert hash_value("test1") != hash_value("test2")
    
    def test_mask_email(self):
        """测试邮箱掩码"""
        assert mask_email("john.doe@example.com") == "j***@example.com"
        assert mask_email("a@b.com") == "a***@b.com"
        assert mask_email("invalid") == "invalid"  # 无效邮箱返回原值
    
    def test_mask_phone(self):
        """测试手机号掩码"""
        assert mask_phone("13812345678") == "138****5678"
        assert mask_phone("12345") == "***"  # 太短
    
    def test_mask_name_chinese(self):
        """测试中文姓名掩码"""
        assert mask_name("张三") == "张*"
        assert mask_name("欧阳修") == "欧**"
    
    def test_mask_name_english(self):
        """测试英文姓名掩码"""
        assert mask_name("John Doe") == "J*** D**"
        assert mask_name("Alice") == "A****"
    
    def test_generalize_age(self):
        """测试年龄泛化"""
        assert generalize_age(25) == "20-29"
        assert generalize_age(35) == "30-39"
        assert generalize_age(25, bucket_size=5) == "25-29"


class TestDeIDRewriter:
    """去标识化重写器测试"""
    
    def setup_method(self):
        self.rewriter = DeIDRewriter()
    
    def test_apply_deid_to_rows(self):
        """测试对结果集应用去标识化"""
        rows = [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
            {"id": 2, "name": "李四", "email": "lisi@example.com"},
        ]
        
        result = self.rewriter.apply_deid(rows)
        
        # 验证脱敏
        assert result[0]["name"] == "张*"
        assert "***@" in result[0]["email"]
        
        # id不应被脱敏
        assert result[0]["id"] == 1
    
    def test_empty_rows(self):
        """测试空结果集"""
        result = self.rewriter.apply_deid([])
        assert result == []
    
    def test_custom_sensitive_columns(self):
        """测试自定义敏感列"""
        rewriter = DeIDRewriter(sensitive_columns={"custom_field": "hash"})
        rows = [{"custom_field": "secret"}]
        
        result = rewriter.apply_deid(rows)
        assert result[0]["custom_field"] != "secret"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

