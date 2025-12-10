"""
ConfigManager - 配置管理器
职责: 加载并管理策略配置文件
"""
import os
from typing import Any, Dict, Optional
from pathlib import Path

import yaml


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "rules": [
            {
                "condition": "aggregations",  # 有聚合函数时
                "action": "DP",
                "params": {"epsilon": 1.0, "mechanism": "laplace"},
            },
            {
                "condition": "sensitive_columns",  # 有敏感列时
                "action": "DeID",
                "params": {"method": "hash"},
            },
        ],
        "sensitive_columns": ["name", "email", "phone", "id_card", "ssn"],
        "default_epsilon": 1.0,
    }
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径 (YAML格式)
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)
    
    def get_rules(self) -> list:
        """获取策略规则列表"""
        return self._config.get("rules", [])
    
    def get_sensitive_columns(self) -> list:
        """获取敏感列列表"""
        return self._config.get("sensitive_columns", [])
    
    def get_default_epsilon(self) -> float:
        """获取默认epsilon值"""
        return self._config.get("default_epsilon", 1.0)
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConfigManager":
        """从字典创建配置管理器"""
        manager = cls()
        manager._config = config_dict
        return manager

