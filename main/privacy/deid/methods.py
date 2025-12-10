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

