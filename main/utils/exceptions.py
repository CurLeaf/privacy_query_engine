"""
Custom Exceptions - 自定义异常类
"""


class PrivacyEngineError(Exception):
    """隐私引擎基础异常"""
    pass


class SQLParseError(PrivacyEngineError):
    """SQL解析错误"""
    pass


class PolicyError(PrivacyEngineError):
    """策略相关错误"""
    pass


class ExecutionError(PrivacyEngineError):
    """执行相关错误"""
    pass


class ConfigurationError(PrivacyEngineError):
    """配置相关错误"""
    pass


class PrivacyBudgetExceededError(PrivacyEngineError):
    """隐私预算超限错误 (用于后续版本)"""
    pass

