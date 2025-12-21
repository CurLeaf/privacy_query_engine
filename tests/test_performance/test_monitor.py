"""
Tests for Performance Monitor (v3.0)
"""
import pytest
import time

from main.performance import PerformanceMonitor, QueryMetrics, QueryCache, RateLimiter


class TestPerformanceMonitor:
    """性能监控器测试"""
    
    def setup_method(self):
        self.monitor = PerformanceMonitor()
    
    def test_start_and_end_query(self):
        """测试开始和结束查询跟踪"""
        metrics = self.monitor.start_query("q1", "user1")
        assert metrics.query_id == "q1"
        assert metrics.user_id == "user1"
        
        time.sleep(0.01)  # 模拟处理时间
        
        result = self.monitor.end_query("q1")
        assert result is not None
        assert result.total_time_ms > 0
    
    def test_record_phase_times(self):
        """测试记录各阶段时间"""
        self.monitor.start_query("q1", "user1")
        
        self.monitor.record_analysis_time("q1", 10.0)
        self.monitor.record_policy_time("q1", 5.0)
        self.monitor.record_execution_time("q1", 50.0)
        self.monitor.record_privacy_time("q1", 15.0)
        
        result = self.monitor.end_query("q1")
        
        assert result.analysis_time_ms == 10.0
        assert result.policy_time_ms == 5.0
        assert result.execution_time_ms == 50.0
        assert result.privacy_time_ms == 15.0
    
    def test_cache_hit_recording(self):
        """测试缓存命中记录"""
        self.monitor.start_query("q1", "user1")
        self.monitor.record_cache_hit("q1", True)
        result = self.monitor.end_query("q1")
        
        assert result.cache_hit is True
        
        stats = self.monitor.get_statistics()
        assert stats["cache_hits"] == 1
    
    def test_slow_query_detection(self):
        """测试慢查询检测"""
        monitor = PerformanceMonitor(slow_query_threshold_ms=10.0)
        
        monitor.start_query("q1", "user1")
        time.sleep(0.02)  # 20ms
        monitor.end_query("q1")
        
        stats = monitor.get_statistics()
        assert stats["slow_queries"] == 1
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        self.monitor.start_query("q1", "user1")
        self.monitor.end_query("q1")
        
        self.monitor.start_query("q2", "user1")
        self.monitor.record_cache_hit("q2", True)
        self.monitor.end_query("q2")
        
        stats = self.monitor.get_statistics()
        
        assert stats["total_queries"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_hit_rate"] == 0.5


class TestQueryCache:
    """查询缓存测试"""
    
    def setup_method(self):
        self.cache = QueryCache()
    
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        self.cache.set("SELECT 1", {"result": 1})
        value = self.cache.get("SELECT 1")
        
        assert value == {"result": 1}
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        value = self.cache.get("SELECT 2")
        assert value is None
    
    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = QueryCache(default_ttl_seconds=0.01)
        cache.set("SELECT 1", {"result": 1})
        
        time.sleep(0.02)
        
        value = cache.get("SELECT 1")
        assert value is None
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = QueryCache(max_entries=2)
        
        cache.set("SELECT 1", 1)
        cache.set("SELECT 2", 2)
        cache.get("SELECT 1")  # 访问SELECT 1使其更新
        cache.set("SELECT 3", 3)  # 应该淘汰SELECT 2
        
        assert cache.get("SELECT 1") == 1
        assert cache.get("SELECT 2") is None
        assert cache.get("SELECT 3") == 3
    
    def test_get_or_compute(self):
        """测试获取或计算"""
        compute_count = [0]
        
        def compute():
            compute_count[0] += 1
            return {"computed": True}
        
        # 第一次调用应该计算
        result1 = self.cache.get_or_compute("SELECT 1", compute)
        assert result1 == {"computed": True}
        assert compute_count[0] == 1
        
        # 第二次调用应该使用缓存
        result2 = self.cache.get_or_compute("SELECT 1", compute)
        assert result2 == {"computed": True}
        assert compute_count[0] == 1  # 没有再次计算
    
    def test_statistics(self):
        """测试缓存统计"""
        self.cache.set("SELECT 1", 1)
        self.cache.get("SELECT 1")  # hit
        self.cache.get("SELECT 2")  # miss
        
        stats = self.cache.get_statistics()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestRateLimiter:
    """速率限制器测试"""
    
    def test_allow_within_limit(self):
        """测试在限制内允许请求"""
        limiter = RateLimiter(requests_per_second=10.0)
        
        result = limiter.check_and_record("user1")
        assert result.allowed is True
    
    def test_reject_over_limit(self):
        """测试超过限制拒绝请求"""
        limiter = RateLimiter(requests_per_second=2.0)
        
        limiter.check_and_record("user1")
        limiter.check_and_record("user1")
        result = limiter.check_and_record("user1")
        
        assert result.allowed is False
        assert result.retry_after > 0
    
    def test_user_rate_limit(self):
        """测试用户级别限制"""
        limiter = RateLimiter(
            requests_per_second=100.0,
            user_requests_per_minute=2.0,
        )
        
        limiter.check_and_record("user1")
        limiter.check_and_record("user1")
        result = limiter.check_and_record("user1")
        
        assert result.allowed is False
        assert "user1" in result.message.lower() or "user" in result.message.lower()
    
    def test_statistics(self):
        """测试统计信息"""
        limiter = RateLimiter(requests_per_second=1.0)
        
        limiter.check_and_record("user1")
        limiter.check_and_record("user1")  # 可能被拒绝
        
        stats = limiter.get_statistics()
        
        assert stats["total_requests"] >= 1
        assert "rejected_requests" in stats
