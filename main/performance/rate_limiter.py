"""
Rate Limiter (v3.0)

查询速率限制和负载管理。
"""
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from threading import Lock
from collections import deque


@dataclass
class RateLimitResult:
    """速率限制结果"""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[float] = None
    message: str = ""


class RateLimiter:
    """
    速率限制器
    
    提供:
    - 滑动窗口速率限制
    - 用户级别限制
    - 全局限制
    - 突发流量处理
    """
    
    def __init__(
        self,
        requests_per_second: float = 10.0,
        requests_per_minute: float = 100.0,
        burst_size: int = 20,
        user_requests_per_minute: float = 50.0,
    ):
        """
        初始化速率限制器
        
        Args:
            requests_per_second: 每秒请求数限制
            requests_per_minute: 每分钟请求数限制
            burst_size: 突发请求大小
            user_requests_per_minute: 每用户每分钟请求数限制
        """
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.user_requests_per_minute = user_requests_per_minute
        
        self._global_requests: deque = deque()
        self._user_requests: Dict[str, deque] = {}
        self._lock = Lock()
        
        # 统计
        self._total_requests = 0
        self._rejected_requests = 0
    
    def _clean_old_requests(self, requests: deque, window_seconds: float):
        """清理过期的请求记录"""
        now = time.time()
        while requests and now - requests[0] > window_seconds:
            requests.popleft()
    
    def _check_rate(
        self,
        requests: deque,
        limit: float,
        window_seconds: float,
    ) -> tuple[bool, int, float]:
        """检查速率限制"""
        now = time.time()
        self._clean_old_requests(requests, window_seconds)
        
        count = len(requests)
        remaining = max(0, int(limit - count))
        
        if count >= limit:
            # 计算重试时间
            if requests:
                oldest = requests[0]
                reset_time = oldest + window_seconds
                retry_after = reset_time - now
            else:
                reset_time = now + window_seconds
                retry_after = window_seconds
            return False, remaining, retry_after
        
        return True, remaining, 0.0
    
    def check(self, user_id: str = None) -> RateLimitResult:
        """
        检查是否允许请求
        
        Args:
            user_id: 用户ID (可选)
            
        Returns:
            RateLimitResult
        """
        with self._lock:
            now = time.time()
            
            # 检查全局每秒限制
            allowed, remaining, retry_after = self._check_rate(
                self._global_requests,
                self.requests_per_second,
                1.0,
            )
            
            if not allowed:
                self._rejected_requests += 1
                return RateLimitResult(
                    allowed=False,
                    remaining=remaining,
                    reset_time=now + retry_after,
                    retry_after=retry_after,
                    message="Global rate limit exceeded (per second)",
                )
            
            # 检查全局每分钟限制
            allowed, remaining, retry_after = self._check_rate(
                self._global_requests,
                self.requests_per_minute,
                60.0,
            )
            
            if not allowed:
                self._rejected_requests += 1
                return RateLimitResult(
                    allowed=False,
                    remaining=remaining,
                    reset_time=now + retry_after,
                    retry_after=retry_after,
                    message="Global rate limit exceeded (per minute)",
                )
            
            # 检查用户限制
            if user_id:
                if user_id not in self._user_requests:
                    self._user_requests[user_id] = deque()
                
                user_requests = self._user_requests[user_id]
                allowed, remaining, retry_after = self._check_rate(
                    user_requests,
                    self.user_requests_per_minute,
                    60.0,
                )
                
                if not allowed:
                    self._rejected_requests += 1
                    return RateLimitResult(
                        allowed=False,
                        remaining=remaining,
                        reset_time=now + retry_after,
                        retry_after=retry_after,
                        message=f"User rate limit exceeded for {user_id}",
                    )
            
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_time=now + 60.0,
                message="Request allowed",
            )
    
    def record(self, user_id: str = None):
        """记录请求"""
        with self._lock:
            now = time.time()
            self._global_requests.append(now)
            self._total_requests += 1
            
            if user_id:
                if user_id not in self._user_requests:
                    self._user_requests[user_id] = deque()
                self._user_requests[user_id].append(now)
    
    def check_and_record(self, user_id: str = None) -> RateLimitResult:
        """检查并记录请求"""
        result = self.check(user_id)
        if result.allowed:
            self.record(user_id)
        return result
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "rejected_requests": self._rejected_requests,
                "rejection_rate": self._rejected_requests / self._total_requests if self._total_requests > 0 else 0,
                "current_global_requests": len(self._global_requests),
                "active_users": len(self._user_requests),
            }
    
    def reset(self):
        """重置限制器（仅用于测试）"""
        with self._lock:
            self._global_requests.clear()
            self._user_requests.clear()
            self._total_requests = 0
            self._rejected_requests = 0


class QueryQueue:
    """
    查询队列
    
    用于高负载场景下的查询排队。
    """
    
    def __init__(self, max_size: int = 100, timeout_seconds: float = 30.0):
        """
        初始化查询队列
        
        Args:
            max_size: 最大队列大小
            timeout_seconds: 队列超时时间
        """
        self._queue: deque = deque()
        self._lock = Lock()
        self.max_size = max_size
        self.timeout_seconds = timeout_seconds
        
        # 统计
        self._total_queued = 0
        self._total_processed = 0
        self._total_timeout = 0
    
    def enqueue(self, query_id: str, user_id: str, priority: int = 0) -> bool:
        """
        将查询加入队列
        
        Args:
            query_id: 查询ID
            user_id: 用户ID
            priority: 优先级 (越高越优先)
            
        Returns:
            是否成功加入队列
        """
        with self._lock:
            if len(self._queue) >= self.max_size:
                return False
            
            entry = {
                "query_id": query_id,
                "user_id": user_id,
                "priority": priority,
                "enqueue_time": time.time(),
            }
            
            # 按优先级插入
            inserted = False
            for i, item in enumerate(self._queue):
                if priority > item["priority"]:
                    self._queue.insert(i, entry)
                    inserted = True
                    break
            
            if not inserted:
                self._queue.append(entry)
            
            self._total_queued += 1
            return True
    
    def dequeue(self) -> Optional[Dict]:
        """从队列取出查询"""
        with self._lock:
            now = time.time()
            
            # 清理超时的查询
            while self._queue:
                entry = self._queue[0]
                if now - entry["enqueue_time"] > self.timeout_seconds:
                    self._queue.popleft()
                    self._total_timeout += 1
                else:
                    break
            
            if not self._queue:
                return None
            
            entry = self._queue.popleft()
            self._total_processed += 1
            return entry
    
    def get_position(self, query_id: str) -> int:
        """获取查询在队列中的位置"""
        with self._lock:
            for i, entry in enumerate(self._queue):
                if entry["query_id"] == query_id:
                    return i
            return -1
    
    def get_statistics(self) -> Dict:
        """获取队列统计"""
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "max_size": self.max_size,
                "total_queued": self._total_queued,
                "total_processed": self._total_processed,
                "total_timeout": self._total_timeout,
            }
