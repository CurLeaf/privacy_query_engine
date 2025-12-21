"""
ConfigManager - 配置管理器 (v3.0 Enhanced)
职责: 加载并管理策略配置文件，支持热重载和高级配置
"""
import os
import re
import time
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from threading import Lock, Thread
from dataclasses import dataclass, field
from enum import Enum

import yaml


class DataClassification(Enum):
    """数据分类级别"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class RoleConfig:
    """角色配置"""
    name: str
    epsilon: float = 1.0
    delta: float = 1e-5
    max_queries_per_day: int = 1000
    allowed_tables: List[str] = field(default_factory=list)
    denied_tables: List[str] = field(default_factory=list)
    allowed_columns: List[str] = field(default_factory=list)
    denied_columns: List[str] = field(default_factory=list)


@dataclass
class ColumnPattern:
    """列模式匹配规则"""
    pattern: str
    classification: DataClassification
    privacy_method: str  # "DP", "DeID", "MASK", "ENCRYPT"
    params: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, column_name: str) -> bool:
        """检查列名是否匹配模式"""
        return bool(re.match(self.pattern, column_name, re.IGNORECASE))


@dataclass
class TablePolicy:
    """表级策略"""
    table_name: str
    classification: DataClassification
    default_epsilon: float = 1.0
    column_policies: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ConfigManager:
    """配置管理器 (v3.0 Enhanced)"""
    
    DEFAULT_CONFIG = {
        "rules": [
            {
                "condition": "aggregations",
                "action": "DP",
                "params": {"epsilon": 1.0, "mechanism": "laplace"},
            },
            {
                "condition": "sensitive_columns",
                "action": "DeID",
                "params": {"method": "hash"},
            },
        ],
        "sensitive_columns": ["name", "email", "phone", "id_card", "ssn"],
        "default_epsilon": 1.0,
        "roles": {},
        "column_patterns": [],
        "table_policies": {},
        "classification_rules": {
            "public": {"epsilon": 2.0, "allow_raw": True},
            "internal": {"epsilon": 1.0, "allow_raw": False},
            "confidential": {"epsilon": 0.5, "allow_raw": False},
            "restricted": {"epsilon": 0.1, "allow_raw": False},
        },
    }
    
    def __init__(self, config_path: str = None, enable_hot_reload: bool = False):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径 (YAML格式)
            enable_hot_reload: 是否启用热重载
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._lock = Lock()
        self._last_modified: float = 0
        self._reload_callbacks: List[Callable] = []
        self._hot_reload_enabled = enable_hot_reload
        self._watcher_thread: Optional[Thread] = None
        self._stop_watcher = False
        
        self._load_config()
        
        if enable_hot_reload and config_path:
            self._start_watcher()
    
    def _load_config(self):
        """加载配置文件"""
        with self._lock:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
                self._last_modified = os.path.getmtime(self.config_path)
            else:
                self._config = self.DEFAULT_CONFIG.copy()
    
    def _start_watcher(self):
        """启动配置文件监视器"""
        def watch():
            while not self._stop_watcher:
                try:
                    if self.config_path and os.path.exists(self.config_path):
                        current_mtime = os.path.getmtime(self.config_path)
                        if current_mtime > self._last_modified:
                            self.reload()
                except Exception:
                    pass
                time.sleep(1)
        
        self._watcher_thread = Thread(target=watch, daemon=True)
        self._watcher_thread.start()
    
    def stop_watcher(self):
        """停止配置文件监视器"""
        self._stop_watcher = True
        if self._watcher_thread:
            self._watcher_thread.join(timeout=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        with self._lock:
            return self._config.get(key, default)
    
    def get_rules(self) -> list:
        """获取策略规则列表"""
        return self.get("rules", [])
    
    def get_sensitive_columns(self) -> list:
        """获取敏感列列表"""
        return self.get("sensitive_columns", [])
    
    def get_default_epsilon(self) -> float:
        """获取默认epsilon值"""
        return self.get("default_epsilon", 1.0)
    
    def get_role_config(self, role_name: str) -> Optional[RoleConfig]:
        """获取角色配置 (v3.0)"""
        roles = self.get("roles", {})
        if role_name not in roles:
            return None
        
        role_data = roles[role_name]
        return RoleConfig(
            name=role_name,
            epsilon=role_data.get("epsilon", 1.0),
            delta=role_data.get("delta", 1e-5),
            max_queries_per_day=role_data.get("max_queries_per_day", 1000),
            allowed_tables=role_data.get("allowed_tables", []),
            denied_tables=role_data.get("denied_tables", []),
            allowed_columns=role_data.get("allowed_columns", []),
            denied_columns=role_data.get("denied_columns", []),
        )
    
    def get_column_patterns(self) -> List[ColumnPattern]:
        """获取列模式匹配规则 (v3.0)"""
        patterns = self.get("column_patterns", [])
        result = []
        for p in patterns:
            result.append(ColumnPattern(
                pattern=p.get("pattern", ""),
                classification=DataClassification(p.get("classification", "internal")),
                privacy_method=p.get("privacy_method", "DeID"),
                params=p.get("params", {}),
            ))
        return result
    
    def get_table_policy(self, table_name: str) -> Optional[TablePolicy]:
        """获取表级策略 (v3.0)"""
        policies = self.get("table_policies", {})
        if table_name not in policies:
            return None
        
        policy_data = policies[table_name]
        return TablePolicy(
            table_name=table_name,
            classification=DataClassification(policy_data.get("classification", "internal")),
            default_epsilon=policy_data.get("default_epsilon", 1.0),
            column_policies=policy_data.get("column_policies", {}),
        )
    
    def get_classification_rules(self, classification: DataClassification) -> Dict[str, Any]:
        """获取分类级别规则 (v3.0)"""
        rules = self.get("classification_rules", {})
        return rules.get(classification.value, {"epsilon": 1.0, "allow_raw": False})
    
    def reload(self):
        """重新加载配置"""
        old_config = self._config.copy()
        self._load_config()
        
        # 触发回调
        for callback in self._reload_callbacks:
            try:
                callback(old_config, self._config)
            except Exception:
                pass
    
    def on_reload(self, callback: Callable):
        """注册重载回调"""
        self._reload_callbacks.append(callback)
    
    def update_config(self, updates: Dict[str, Any]):
        """动态更新配置 (v3.0)"""
        with self._lock:
            self._config.update(updates)
            
            # 如果有配置文件，保存更新
            if self.config_path:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConfigManager":
        """从字典创建配置管理器"""
        manager = cls()
        manager._config = config_dict
        return manager


