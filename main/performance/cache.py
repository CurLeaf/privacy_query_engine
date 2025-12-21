"""
Query Cache (v3.0)

查询分析结果缓存和敏感度计算复用。
"""
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from threading import Lock
from collections import OrderedDict


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: float = 300.0  # 默认5分钟
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class QueryCache:
    """
    查询缓存
    
    提供:
    - SQL分析结果缓存
    - 敏感度计算复用
    - LRU淘汰策略
    - 内存限制
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        max_memory_mb: float = 50.0,
        default_ttl_seconds: float = 300.0,
    ):
        """
        初始化查询缓存
        
        Args:
            max_entries: 最大缓存条目数
            max_memory_mb: 最大内存使用(MB)
            default_ttl_seconds: 默认TTL(秒)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self.max_entries = max_entries
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.default_ttl_seconds = default_ttl_seconds
        
        # 统计
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._current_memory = 0
    
    def _generate_key(self, sql: str, context: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        content = sql
        if context:
            content += str(sorted(context.items()))
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小"""
        import sys
        try:
            return sys.getsizeof(value)
        except TypeError:
            return 1024  # 默认1KB
    
    def _evict_if_needed(self):
        """如果需要则淘汰条目"""
        # 淘汰过期条目
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            self._remove(key)
        
        # 如果仍然超过限制，使用LRU淘汰
        while len(self._cache) >= self.max_entries:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
        
        # 检查内存限制
        while self._current_memory > self.max_memory_bytes and self._cache:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
    
    def _remove(self, key: str):
        """移除缓存条目"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_memory -= entry.size_bytes
            self._evictions += 1
    
    def get(self, sql: str, context: Dict[str, Any] = None) -> Optional[Any]:
        """获取缓存值"""
        key = self._generate_key(sql, context)
        
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if entry.is_expired():
                self._remove(key)
                self._misses += 1
                return None
            
            # 更新访问信息并移到末尾(LRU)
            entry.touch()
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.value
    
    def set(
        self,
        sql: str,
        value: Any,
        context: Dict[str, Any] = None,
        ttl_seconds: float = None,
    ):
        """设置缓存值"""
        key = self._generate_key(sql, context)
        size = self._estimate_size(value)
        
        with self._lock:
            # 如果已存在，先移除
            if key in self._cache:
                self._remove(key)
            
            # 淘汰旧条目
            self._evict_if_needed()
            
            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds or self.default_ttl_seconds,
                size_bytes=size,
            )
            
            self._cache[key] = entry
            self._current_memory += size
    
    def invalidate(self, sql: str, context: Dict[str, Any] = None):
        """使缓存失效"""
        key = self._generate_key(sql, context)
        
        with self._lock:
            self._remove(key)
    
    def invalidate_all(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries,
                "memory_bytes": self._current_memory,
                "max_memory_bytes": self.max_memory_bytes,
                "memory_usage_percent": (self._current_memory / self.max_memory_bytes * 100) if self.max_memory_bytes > 0 else 0,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
            }
    
    def get_or_compute(
        self,
        sql: str,
        compute_fn,
        context: Dict[str, Any] = None,
        ttl_seconds: float = None,
    ) -> Any:
        """获取缓存值，如果不存在则计算并缓存"""
        value = self.get(sql, context)
        if value is not None:
            return value
        
        # 计算值
        value = compute_fn()
        
        # 缓存结果
        self.set(sql, value, context, ttl_seconds)
        
        return value


class SensitivityCache(QueryCache):
    """
    敏感度计算缓存
    
    专门用于缓存敏感度计算结果。
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def get_sensitivity(
        self,
        table: str,
        column: str,
        aggregation: str,
    ) -> Optional[float]:
        """获取缓存的敏感度"""
        key = f"{table}.{column}.{aggregation}"
        return self.get(key)
    
    def set_sensitivity(
        self,
        table: str,
        column: str,
        aggregation: str,
        sensitivity: float,
        ttl_seconds: float = None,
    ):
        """缓存敏感度"""
        key = f"{table}.{column}.{aggregation}"
        self.set(key, sensitivity, ttl_seconds=ttl_seconds)
