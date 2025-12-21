"""
Load Balancer (v3.0)

负载均衡器，支持多种负载均衡策略。
"""
import random
from enum import Enum
from typing import List, Optional
from threading import Lock

from .coordinator import ServiceInstance, InstanceStatus


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"


class LoadBalancer:
    """
    负载均衡器
    
    提供:
    - 多种负载均衡策略
    - 自动故障转移
    - 权重支持
    """
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        """
        初始化负载均衡器
        
        Args:
            strategy: 负载均衡策略
        """
        self.strategy = strategy
        self._lock = Lock()
        self._round_robin_index = 0
        self._connection_counts: dict = {}
    
    def select(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """
        选择一个实例
        
        Args:
            instances: 可用实例列表
            
        Returns:
            选中的实例，如果没有可用实例则返回None
        """
        # 过滤健康的实例
        healthy = [i for i in instances if i.status == InstanceStatus.HEALTHY]
        
        if not healthy:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(healthy)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(healthy)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random(healthy)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
            return self._weighted_random(healthy)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(healthy)
        else:
            return self._round_robin(healthy)
    
    def _round_robin(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """轮询策略"""
        with self._lock:
            index = self._round_robin_index % len(instances)
            self._round_robin_index += 1
            return instances[index]
    
    def _weighted_round_robin(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """加权轮询策略"""
        # 构建加权列表
        weighted_list = []
        for inst in instances:
            weighted_list.extend([inst] * inst.weight)
        
        if not weighted_list:
            return instances[0]
        
        with self._lock:
            index = self._round_robin_index % len(weighted_list)
            self._round_robin_index += 1
            return weighted_list[index]
    
    def _random(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """随机策略"""
        return random.choice(instances)
    
    def _weighted_random(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """加权随机策略"""
        total_weight = sum(i.weight for i in instances)
        if total_weight == 0:
            return random.choice(instances)
        
        r = random.uniform(0, total_weight)
        cumulative = 0
        
        for inst in instances:
            cumulative += inst.weight
            if r <= cumulative:
                return inst
        
        return instances[-1]
    
    def _least_connections(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """最少连接策略"""
        with self._lock:
            # 初始化连接计数
            for inst in instances:
                if inst.instance_id not in self._connection_counts:
                    self._connection_counts[inst.instance_id] = 0
            
            # 找到连接数最少的实例
            min_conn = float('inf')
            selected = instances[0]
            
            for inst in instances:
                conn = self._connection_counts.get(inst.instance_id, 0)
                if conn < min_conn:
                    min_conn = conn
                    selected = inst
            
            return selected
    
    def record_connection(self, instance_id: str):
        """记录连接"""
        with self._lock:
            self._connection_counts[instance_id] = self._connection_counts.get(instance_id, 0) + 1
    
    def release_connection(self, instance_id: str):
        """释放连接"""
        with self._lock:
            if instance_id in self._connection_counts:
                self._connection_counts[instance_id] = max(0, self._connection_counts[instance_id] - 1)
    
    def get_connection_counts(self) -> dict:
        """获取连接计数"""
        with self._lock:
            return self._connection_counts.copy()
    
    def reset(self):
        """重置负载均衡器状态"""
        with self._lock:
            self._round_robin_index = 0
            self._connection_counts.clear()
