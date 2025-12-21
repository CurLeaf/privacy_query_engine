"""
De-Identification Methods - 去标识化方法
提供多种脱敏函数
"""
import hashlib
from typing import Any


def hash_value(value: Any, length: int = 16) -> str:
    """
    对值进行SHA256哈希
    
    Args:
        value: 待哈希的值
        length: 返回的哈希长度 (截取前N位)
        
    Returns:
        哈希后的字符串
    """
    if value is None:
        return None
    hash_full = hashlib.sha256(str(value).encode()).hexdigest()
    return hash_full[:length]


def mask_email(email: str) -> str:
    """
    对邮箱地址进行掩码
    
    Example:
        "john.doe@example.com" -> "j***@example.com"
    """
    if not email or "@" not in email:
        return email
    
    local, domain = email.split("@", 1)
    if len(local) > 0:
        masked_local = local[0] + "***"
    else:
        masked_local = "***"
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    对手机号进行掩码
    
    Example:
        "13812345678" -> "138****5678"
    """
    if not phone:
        return phone
    
    # 移除非数字字符
    digits = "".join(filter(str.isdigit, phone))
    
    if len(digits) < 7:
        return "***"
    
    # 保留前3位和后4位
    return digits[:3] + "****" + digits[-4:]


def mask_name(name: str) -> str:
    """
    对姓名进行掩码
    
    Example:
        "张三" -> "张*"
        "John Doe" -> "J*** D**"
    """
    if not name:
        return name
    
    # 处理中文名
    if any("\u4e00" <= char <= "\u9fff" for char in name):
        if len(name) >= 2:
            return name[0] + "*" * (len(name) - 1)
        return "*"
    
    # 处理英文名
    parts = name.split()
    masked_parts = []
    for part in parts:
        if len(part) > 0:
            masked_parts.append(part[0] + "*" * (len(part) - 1))
    
    return " ".join(masked_parts)


def generalize_age(age: int, bucket_size: int = 10) -> str:
    """
    对年龄进行泛化
    
    Example:
        25, bucket_size=10 -> "20-29"
        35, bucket_size=5  -> "35-39"
    """
    if age is None or not isinstance(age, (int, float)):
        return None
    
    age = int(age)
    lower = (age // bucket_size) * bucket_size
    upper = lower + bucket_size - 1
    
    return f"{lower}-{upper}"


def format_preserving_encrypt(value: str, key: bytes = None, alphabet: str = None) -> str:
    """
    格式保留加密 - 保持原始格式的加密
    
    Args:
        value: 待加密的值
        key: 加密密钥 (如果为None则使用默认密钥)
        alphabet: 允许的字符集 (如果为None则自动检测)
        
    Returns:
        加密后的值，保持原始格式
        
    Example:
        "123-45-6789" -> "847-29-3156" (SSN格式保留)
    """
    if not value:
        return value
    
    if key is None:
        key = b"default_fpe_key_32bytes_long!!"
    
    # 简化实现：使用确定性的伪随机置换
    import struct
    
    # 提取数字和非数字部分
    result = []
    digits = []
    digit_positions = []
    
    for i, char in enumerate(value):
        if char.isdigit():
            digits.append(char)
            digit_positions.append(i)
            result.append(None)  # 占位符
        else:
            result.append(char)
    
    if not digits:
        return value
    
    # 使用密钥和原始值生成确定性的置换
    seed_data = key + value.encode()
    seed_hash = hashlib.sha256(seed_data).digest()
    seed_int = struct.unpack('>Q', seed_hash[:8])[0]
    
    # 简单的确定性数字置换
    import random
    rng = random.Random(seed_int)
    
    # 对数字进行置换
    digit_str = ''.join(digits)
    digit_int = int(digit_str) if digit_str else 0
    
    # 生成新的数字序列
    new_digits = []
    for _ in digits:
        new_digits.append(str(rng.randint(0, 9)))
    
    # 将新数字放回原位置
    for i, pos in enumerate(digit_positions):
        result[pos] = new_digits[i]
    
    return ''.join(result)


def date_shift(date_value, individual_id: str, max_shift_days: int = 30) -> Any:
    """
    日期偏移 - 对同一个人的所有日期应用一致的偏移
    
    Args:
        date_value: 日期值 (datetime, date, 或字符串)
        individual_id: 个人标识符 (用于生成一致的偏移)
        max_shift_days: 最大偏移天数
        
    Returns:
        偏移后的日期
    """
    from datetime import datetime, date, timedelta
    
    if date_value is None:
        return None
    
    # 转换为datetime对象
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except ValueError:
            try:
                date_value = datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                return date_value
    elif isinstance(date_value, date) and not isinstance(date_value, datetime):
        date_value = datetime.combine(date_value, datetime.min.time())
    
    # 基于individual_id生成确定性的偏移量
    hash_bytes = hashlib.sha256(individual_id.encode()).digest()
    import struct
    offset_seed = struct.unpack('>i', hash_bytes[:4])[0]
    
    # 计算偏移天数 (-max_shift_days 到 +max_shift_days)
    offset_days = (offset_seed % (2 * max_shift_days + 1)) - max_shift_days
    
    return date_value + timedelta(days=offset_days)


def geographic_generalize(address: str, level: str = "city") -> str:
    """
    地理位置泛化 - 将详细地址泛化到更高级别
    
    Args:
        address: 地址字符串
        level: 泛化级别 ("zip3", "zip5", "city", "state", "country")
        
    Returns:
        泛化后的地址
        
    Example:
        "123 Main St, New York, NY 10001" with level="city" -> "New York, NY"
    """
    if not address:
        return address
    
    # 简化实现：基于逗号分割和级别进行泛化
    parts = [p.strip() for p in address.split(',')]
    
    if level == "zip3":
        # 保留邮编前3位
        for i, part in enumerate(parts):
            # 查找邮编模式
            import re
            zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', part)
            if zip_match:
                zip_code = zip_match.group(1)
                parts[i] = part.replace(zip_code, zip_code[:3] + "XX")
        return ', '.join(parts)
    
    elif level == "zip5":
        # 移除邮编后4位
        for i, part in enumerate(parts):
            import re
            parts[i] = re.sub(r'(\d{5})-\d{4}', r'\1', part)
        return ', '.join(parts)
    
    elif level == "city":
        # 只保留城市和州
        if len(parts) >= 2:
            return ', '.join(parts[-2:])
        return address
    
    elif level == "state":
        # 只保留州
        if len(parts) >= 1:
            return parts[-1]
        return address
    
    elif level == "country":
        return "USA"  # 简化实现
    
    return address


def suppress_rare_values(value: Any, value_counts: dict, threshold: int = 5) -> Any:
    """
    稀有值抑制 - 将出现次数低于阈值的值替换为通用值
    
    Args:
        value: 待检查的值
        value_counts: 值计数字典 {value: count}
        threshold: 最小出现次数阈值
        
    Returns:
        原值或抑制后的值 ("*SUPPRESSED*")
    """
    if value is None:
        return None
    
    count = value_counts.get(value, 0)
    
    if count < threshold:
        return "*SUPPRESSED*"
    
    return value


class KAnonymizer:
    """
    K-匿名化处理器
    确保每条记录与至少k-1条其他记录在准标识符上不可区分
    """
    
    def __init__(self, k: int = 5):
        """
        初始化K-匿名化器
        
        Args:
            k: K值，每个等价类的最小大小
        """
        self.k = k
    
    def anonymize(
        self,
        data: list,
        quasi_identifiers: list,
        generalization_rules: dict = None
    ) -> list:
        """
        对数据进行K-匿名化
        
        Args:
            data: 数据列表 (每个元素是一个字典)
            quasi_identifiers: 准标识符列表
            generalization_rules: 泛化规则 {column: function}
            
        Returns:
            K-匿名化后的数据
        """
        if not data:
            return data
        
        if generalization_rules is None:
            generalization_rules = {}
        
        # 复制数据
        result = [row.copy() for row in data]
        
        # 对准标识符应用泛化
        for qi in quasi_identifiers:
            if qi in generalization_rules:
                gen_func = generalization_rules[qi]
                for row in result:
                    if qi in row:
                        row[qi] = gen_func(row[qi])
        
        # 检查等价类大小
        equivalence_classes = self._compute_equivalence_classes(result, quasi_identifiers)
        
        # 抑制小于k的等价类
        small_classes = {
            key for key, rows in equivalence_classes.items()
            if len(rows) < self.k
        }
        
        # 标记需要抑制的行
        for row in result:
            key = self._get_equivalence_key(row, quasi_identifiers)
            if key in small_classes:
                for qi in quasi_identifiers:
                    if qi in row:
                        row[qi] = "*SUPPRESSED*"
        
        return result
    
    def _compute_equivalence_classes(self, data: list, quasi_identifiers: list) -> dict:
        """计算等价类"""
        classes = {}
        for i, row in enumerate(data):
            key = self._get_equivalence_key(row, quasi_identifiers)
            if key not in classes:
                classes[key] = []
            classes[key].append(i)
        return classes
    
    def _get_equivalence_key(self, row: dict, quasi_identifiers: list) -> tuple:
        """获取行的等价类键"""
        return tuple(row.get(qi, None) for qi in quasi_identifiers)
    
    def check_k_anonymity(self, data: list, quasi_identifiers: list) -> bool:
        """检查数据是否满足K-匿名性"""
        classes = self._compute_equivalence_classes(data, quasi_identifiers)
        return all(len(rows) >= self.k for rows in classes.values())


class LDiversifier:
    """
    L-多样性处理器
    确保每个等价类中敏感属性至少有l个不同的值
    """
    
    def __init__(self, l: int = 3):
        """
        初始化L-多样性处理器
        
        Args:
            l: L值，每个等价类中敏感属性的最小不同值数量
        """
        self.l = l
    
    def check_l_diversity(
        self,
        data: list,
        quasi_identifiers: list,
        sensitive_attribute: str
    ) -> bool:
        """
        检查数据是否满足L-多样性
        
        Args:
            data: 数据列表
            quasi_identifiers: 准标识符列表
            sensitive_attribute: 敏感属性名
            
        Returns:
            是否满足L-多样性
        """
        classes = self._compute_equivalence_classes(data, quasi_identifiers)
        
        for key, row_indices in classes.items():
            sensitive_values = set()
            for idx in row_indices:
                if sensitive_attribute in data[idx]:
                    sensitive_values.add(data[idx][sensitive_attribute])
            
            if len(sensitive_values) < self.l:
                return False
        
        return True
    
    def diversify(
        self,
        data: list,
        quasi_identifiers: list,
        sensitive_attribute: str
    ) -> list:
        """
        对数据进行L-多样性处理
        
        Args:
            data: 数据列表
            quasi_identifiers: 准标识符列表
            sensitive_attribute: 敏感属性名
            
        Returns:
            处理后的数据 (不满足L-多样性的记录被抑制)
        """
        if not data:
            return data
        
        result = [row.copy() for row in data]
        classes = self._compute_equivalence_classes(result, quasi_identifiers)
        
        # 找出不满足L-多样性的等价类
        non_diverse_classes = set()
        for key, row_indices in classes.items():
            sensitive_values = set()
            for idx in row_indices:
                if sensitive_attribute in result[idx]:
                    sensitive_values.add(result[idx][sensitive_attribute])
            
            if len(sensitive_values) < self.l:
                non_diverse_classes.add(key)
        
        # 抑制不满足条件的记录
        for row in result:
            key = self._get_equivalence_key(row, quasi_identifiers)
            if key in non_diverse_classes:
                if sensitive_attribute in row:
                    row[sensitive_attribute] = "*SUPPRESSED*"
        
        return result
    
    def _compute_equivalence_classes(self, data: list, quasi_identifiers: list) -> dict:
        """计算等价类"""
        classes = {}
        for i, row in enumerate(data):
            key = self._get_equivalence_key(row, quasi_identifiers)
            if key not in classes:
                classes[key] = []
            classes[key].append(i)
        return classes
    
    def _get_equivalence_key(self, row: dict, quasi_identifiers: list) -> tuple:
        """获取行的等价类键"""
        return tuple(row.get(qi, None) for qi in quasi_identifiers)

