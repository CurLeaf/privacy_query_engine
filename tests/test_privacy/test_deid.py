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



class TestAdvancedDeIDMethods:
    """高级去标识化方法测试"""
    
    def test_format_preserving_encrypt(self):
        """测试格式保留加密"""
        from main.privacy.deid import format_preserving_encrypt
        
        # SSN格式
        ssn = "123-45-6789"
        encrypted = format_preserving_encrypt(ssn)
        
        assert len(encrypted) == len(ssn)
        assert encrypted[3] == "-"
        assert encrypted[6] == "-"
        assert encrypted != ssn
    
    def test_format_preserving_encrypt_deterministic(self):
        """测试格式保留加密的确定性"""
        from main.privacy.deid import format_preserving_encrypt
        
        value = "12345"
        key = b"test_key_32_bytes_long_here!!"
        
        result1 = format_preserving_encrypt(value, key)
        result2 = format_preserving_encrypt(value, key)
        
        assert result1 == result2
    
    def test_date_shift(self):
        """测试日期偏移"""
        from main.privacy.deid import date_shift
        from datetime import datetime
        
        date = datetime(2023, 6, 15)
        shifted = date_shift(date, "user123", max_shift_days=30)
        
        assert shifted is not None
        # 偏移应该在范围内
        diff = abs((shifted - date).days)
        assert diff <= 30
    
    def test_date_shift_consistent(self):
        """测试日期偏移的一致性"""
        from main.privacy.deid import date_shift
        from datetime import datetime
        
        date1 = datetime(2023, 6, 15)
        date2 = datetime(2023, 7, 20)
        
        # 同一个人的日期应该有相同的偏移
        shifted1 = date_shift(date1, "user123")
        shifted2 = date_shift(date2, "user123")
        
        offset1 = (shifted1 - date1).days
        offset2 = (shifted2 - date2).days
        
        assert offset1 == offset2
    
    def test_geographic_generalize_city(self):
        """测试地理位置泛化到城市级别"""
        from main.privacy.deid import geographic_generalize
        
        address = "123 Main St, New York, NY 10001"
        generalized = geographic_generalize(address, level="city")
        
        assert "123 Main St" not in generalized
        assert "New York" in generalized or "NY" in generalized
    
    def test_suppress_rare_values(self):
        """测试稀有值抑制"""
        from main.privacy.deid import suppress_rare_values
        
        value_counts = {"common": 100, "rare": 2}
        
        assert suppress_rare_values("common", value_counts, threshold=5) == "common"
        assert suppress_rare_values("rare", value_counts, threshold=5) == "*SUPPRESSED*"


class TestKAnonymizer:
    """K-匿名化测试"""
    
    def test_k_anonymity_check(self):
        """测试K-匿名性检查"""
        from main.privacy.deid import KAnonymizer
        
        anonymizer = KAnonymizer(k=2)
        
        # 满足2-匿名性的数据
        data = [
            {"age": "20-29", "zip": "100XX", "disease": "flu"},
            {"age": "20-29", "zip": "100XX", "disease": "cold"},
            {"age": "30-39", "zip": "200XX", "disease": "flu"},
            {"age": "30-39", "zip": "200XX", "disease": "cold"},
        ]
        
        assert anonymizer.check_k_anonymity(data, ["age", "zip"])
    
    def test_k_anonymity_fail(self):
        """测试K-匿名性检查失败"""
        from main.privacy.deid import KAnonymizer
        
        anonymizer = KAnonymizer(k=3)
        
        # 不满足3-匿名性的数据
        data = [
            {"age": "20-29", "zip": "100XX", "disease": "flu"},
            {"age": "20-29", "zip": "100XX", "disease": "cold"},
            {"age": "30-39", "zip": "200XX", "disease": "flu"},
        ]
        
        assert not anonymizer.check_k_anonymity(data, ["age", "zip"])


class TestLDiversifier:
    """L-多样性测试"""
    
    def test_l_diversity_check(self):
        """测试L-多样性检查"""
        from main.privacy.deid import LDiversifier
        
        diversifier = LDiversifier(l=2)
        
        # 满足2-多样性的数据
        data = [
            {"age": "20-29", "disease": "flu"},
            {"age": "20-29", "disease": "cold"},
            {"age": "30-39", "disease": "flu"},
            {"age": "30-39", "disease": "cold"},
        ]
        
        assert diversifier.check_l_diversity(data, ["age"], "disease")
    
    def test_l_diversity_fail(self):
        """测试L-多样性检查失败"""
        from main.privacy.deid import LDiversifier
        
        diversifier = LDiversifier(l=2)
        
        # 不满足2-多样性的数据 (同一等价类只有一种疾病)
        data = [
            {"age": "20-29", "disease": "flu"},
            {"age": "20-29", "disease": "flu"},
        ]
        
        assert not diversifier.check_l_diversity(data, ["age"], "disease")
