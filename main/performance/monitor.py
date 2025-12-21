"""
Performance Monitor (v3.0)

查询性能监控和指标收集。
"""
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from threading import Lock
from collections import deque


@dataclass
class QueryMetrics:
    """查询性能指标"""
    query_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    analysis_time_ms: float = 0.0
    policy_time_ms: float = 0.0
    execution_time_ms: float = 0.0
    privacy_time_ms: float = 0.0
    total_time_ms: float = 0.0
    result_size_bytes: int = 0
    cache_hit: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "analysis_time_ms": self.analysis_time_ms,
            "policy_time_ms": self.policy_time_ms,
            "execution_time_ms": self.execution_time_ms,
            "privacy_time_ms": self.privacy_time_ms,
            "total_time_ms": self.total_time_ms,
            "result_size_bytes": self.result_size_bytes,
            "cache_hit": self.cache_hit,
            "error": self.error,
        }


class PerformanceMonitor:
    """
    性能监控器
    
    提供:
    - 查询性能跟踪
    - 指标收集和聚合
    - 性能阈值告警
    - 内存使用监控
    """
    
    def __init__(
        self,
        max_metrics: int = 10000,
        slow_query_threshold_ms: float = 1000.0,
        memory_limit_mb: float = 100.0,
    ):
        """
        初始化性能监控器
        
        Args:
            max_metrics: 保留的最大指标数量
            slow_query_threshold_ms: 慢查询阈值(毫秒)
            memory_limit_mb: 内存限制(MB)
        """
        self._metrics: deque = deque(maxlen=max_metrics)
        self._active_queries: Dict[str, QueryMetrics] = {}
        self._lock = Lock()
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.memory_limit_mb = memory_limit_mb
        
        # 聚合统计
        self._total_queries = 0
        self._total_time_ms = 0.0
        self._cache_hits = 0
        self._slow_queries = 0
        self._errors = 0
    
    def start_query(self, query_id: str, user_id: str) -> QueryMetrics:
        """开始跟踪查询"""
        metrics = QueryMetrics(
            query_id=query_id,
            user_id=user_id,
            start_time=datetime.now(),
        )
        
        with self._lock:
            self._active_queries[query_id] = metrics
        
        return metrics
    
    def record_analysis_time(self, query_id: str, time_ms: float):
        """记录分析时间"""
        with self._lock:
            if query_id in self._active_queries:
                self._active_queries[query_id].analysis_time_ms = time_ms
    
    def record_policy_time(self, query_id: str, time_ms: float):
        """记录策略评估时间"""
        with self._lock:
            if query_id in self._active_queries:
                self._active_queries[query_id].policy_time_ms = time_ms
    
    def record_execution_time(self, query_id: str, time_ms: float):
        """记录执行时间"""
        with self._lock:
            if query_id in self._active_queries:
                self._active_queries[query_id].execution_time_ms = time_ms
    
    def record_privacy_time(self, query_id: str, time_ms: float):
        """记录隐私处理时间"""
        with self._lock:
            if query_id in self._active_queries:
                self._active_queries[query_id].privacy_time_ms = time_ms
    
    def record_cache_hit(self, query_id: str, hit: bool):
        """记录缓存命中"""
        with self._lock:
            if query_id in self._active_queries:
                self._active_queries[query_id].cache_hit = hit
    
    def record_result_size(self, query_id: str, size_bytes: int):
        """记录结果大小"""
        with self._lock:
            if query_id in self._active_queries:
                self._active_queries[query_id].result_size_bytes = size_bytes
    
    def record_error(self, query_id: str, error: str):
        """记录错误"""
        with self._lock:
            if query_id in self._active_queries:
                self._active_queries[query_id].error = error
    
    def end_query(self, query_id: str) -> Optional[QueryMetrics]:
        """结束查询跟踪"""
        with self._lock:
            if query_id not in self._active_queries:
                return None
            
            metrics = self._active_queries.pop(query_id)
            metrics.end_time = datetime.now()
            
            # 计算总时间
            delta = metrics.end_time - metrics.start_time
            metrics.total_time_ms = delta.total_seconds() * 1000
            
            # 更新聚合统计
            self._total_queries += 1
            self._total_time_ms += metrics.total_time_ms
            
            if metrics.cache_hit:
                self._cache_hits += 1
            
            if metrics.total_time_ms > self.slow_query_threshold_ms:
                self._slow_queries += 1
            
            if metrics.error:
                self._errors += 1
            
            # 保存指标
            self._metrics.append(metrics)
            
            return metrics
    
    def get_metrics(self, limit: int = 100) -> List[QueryMetrics]:
        """获取最近的指标"""
        with self._lock:
            return list(self._metrics)[-limit:]
    
    def get_metrics_by_user(self, user_id: str, limit: int = 100) -> List[QueryMetrics]:
        """获取指定用户的指标"""
        with self._lock:
            user_metrics = [m for m in self._metrics if m.user_id == user_id]
            return user_metrics[-limit:]
    
    def get_slow_queries(self, limit: int = 100) -> List[QueryMetrics]:
        """获取慢查询"""
        with self._lock:
            slow = [m for m in self._metrics if m.total_time_ms > self.slow_query_threshold_ms]
            return slow[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取性能统计"""
        with self._lock:
            avg_time = self._total_time_ms / self._total_queries if self._total_queries > 0 else 0
            cache_hit_rate = self._cache_hits / self._total_queries if self._total_queries > 0 else 0
            error_rate = self._errors / self._total_queries if self._total_queries > 0 else 0
            
            return {
                "total_queries": self._total_queries,
                "total_time_ms": self._total_time_ms,
                "average_time_ms": avg_time,
                "cache_hits": self._cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "slow_queries": self._slow_queries,
                "slow_query_rate": self._slow_queries / self._total_queries if self._total_queries > 0 else 0,
                "errors": self._errors,
                "error_rate": error_rate,
                "active_queries": len(self._active_queries),
            }
    
    def get_percentiles(self) -> Dict[str, float]:
        """获取响应时间百分位数"""
        with self._lock:
            if not self._metrics:
                return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
            
            times = sorted([m.total_time_ms for m in self._metrics])
            n = len(times)
            
            return {
                "p50": times[int(n * 0.5)] if n > 0 else 0,
                "p90": times[int(n * 0.9)] if n > 0 else 0,
                "p95": times[int(n * 0.95)] if n > 0 else 0,
                "p99": times[int(n * 0.99)] if n > 0 else 0,
            }
    
    def is_slow_query(self, total_time_ms: float) -> bool:
        """判断是否为慢查询"""
        return total_time_ms > self.slow_query_threshold_ms
    
    def clear(self):
        """清空指标（仅用于测试）"""
        with self._lock:
            self._metrics.clear()
            self._active_queries.clear()
            self._total_queries = 0
            self._total_time_ms = 0.0
            self._cache_hits = 0
            self._slow_queries = 0
            self._errors = 0


class PerformanceTimer:
    """性能计时器上下文管理器"""
    
    def __init__(self, monitor: PerformanceMonitor, query_id: str, phase: str):
        self.monitor = monitor
        self.query_id = query_id
        self.phase = phase
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        
        if self.phase == "analysis":
            self.monitor.record_analysis_time(self.query_id, elapsed_ms)
        elif self.phase == "policy":
            self.monitor.record_policy_time(self.query_id, elapsed_ms)
        elif self.phase == "execution":
            self.monitor.record_execution_time(self.query_id, elapsed_ms)
        elif self.phase == "privacy":
            self.monitor.record_privacy_time(self.query_id, elapsed_ms)
