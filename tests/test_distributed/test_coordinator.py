"""
Tests for Distributed System (v3.0)
"""
import pytest
import time

from main.distributed import (
    DistributedCoordinator,
    ServiceInstance,
    InstanceStatus,
    LoadBalancer,
    LoadBalancingStrategy,
    DistributedBudgetSync,
)


class TestDistributedCoordinator:
    """分布式协调器测试"""
    
    def setup_method(self):
        self.coordinator = DistributedCoordinator()
    
    def test_register_instance(self):
        """测试注册实例"""
        instance = self.coordinator.register("localhost", 8080)
        
        assert instance.host == "localhost"
        assert instance.port == 8080
        assert instance.status == InstanceStatus.HEALTHY
    
    def test_deregister_instance(self):
        """测试注销实例"""
        instance = self.coordinator.register("localhost", 8080)
        
        result = self.coordinator.deregister(instance.instance_id)
        assert result is True
        
        assert self.coordinator.get_instance(instance.instance_id) is None
    
    def test_heartbeat(self):
        """测试心跳"""
        instance = self.coordinator.register("localhost", 8080)
        old_heartbeat = instance.last_heartbeat
        
        time.sleep(0.01)
        self.coordinator.heartbeat(instance.instance_id)
        
        updated = self.coordinator.get_instance(instance.instance_id)
        assert updated.last_heartbeat > old_heartbeat
    
    def test_get_healthy_instances(self):
        """测试获取健康实例"""
        inst1 = self.coordinator.register("localhost", 8080)
        inst2 = self.coordinator.register("localhost", 8081)
        
        self.coordinator.set_instance_status(inst2.instance_id, InstanceStatus.UNHEALTHY)
        
        healthy = self.coordinator.get_healthy_instances()
        assert len(healthy) == 1
        assert healthy[0].instance_id == inst1.instance_id
    
    def test_drain_instance(self):
        """测试排空实例"""
        instance = self.coordinator.register("localhost", 8080)
        
        self.coordinator.drain_instance(instance.instance_id)
        
        updated = self.coordinator.get_instance(instance.instance_id)
        assert updated.status == InstanceStatus.DRAINING
    
    def test_statistics(self):
        """测试统计信息"""
        self.coordinator.register("localhost", 8080)
        self.coordinator.register("localhost", 8081)
        
        stats = self.coordinator.get_statistics()
        
        assert stats["total_instances"] == 2
        assert stats["healthy_instances"] == 2


class TestLoadBalancer:
    """负载均衡器测试"""
    
    def setup_method(self):
        self.instances = [
            ServiceInstance("inst1", "localhost", 8080, InstanceStatus.HEALTHY, weight=100),
            ServiceInstance("inst2", "localhost", 8081, InstanceStatus.HEALTHY, weight=100),
            ServiceInstance("inst3", "localhost", 8082, InstanceStatus.HEALTHY, weight=100),
        ]
    
    def test_round_robin(self):
        """测试轮询策略"""
        lb = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        selected = [lb.select(self.instances) for _ in range(6)]
        
        # 应该循环选择
        assert selected[0].instance_id == selected[3].instance_id
        assert selected[1].instance_id == selected[4].instance_id
    
    def test_random(self):
        """测试随机策略"""
        lb = LoadBalancer(LoadBalancingStrategy.RANDOM)
        
        selected = lb.select(self.instances)
        assert selected in self.instances
    
    def test_weighted_random(self):
        """测试加权随机策略"""
        # 设置不同权重
        self.instances[0].weight = 100
        self.instances[1].weight = 1
        self.instances[2].weight = 1
        
        lb = LoadBalancer(LoadBalancingStrategy.WEIGHTED_RANDOM)
        
        # 多次选择，高权重实例应该被选中更多
        selections = [lb.select(self.instances).instance_id for _ in range(100)]
        inst1_count = selections.count("inst1")
        
        # inst1 应该被选中大多数时候
        assert inst1_count > 50
    
    def test_skip_unhealthy(self):
        """测试跳过不健康实例"""
        self.instances[0].status = InstanceStatus.UNHEALTHY
        self.instances[1].status = InstanceStatus.UNHEALTHY
        
        lb = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        selected = lb.select(self.instances)
        assert selected.instance_id == "inst3"
    
    def test_no_healthy_instances(self):
        """测试没有健康实例"""
        for inst in self.instances:
            inst.status = InstanceStatus.UNHEALTHY
        
        lb = LoadBalancer()
        selected = lb.select(self.instances)
        
        assert selected is None


class TestDistributedBudgetSync:
    """分布式预算同步测试"""
    
    def setup_method(self):
        self.sync = DistributedBudgetSync("instance1")
    
    def test_set_and_get_budget(self):
        """测试设置和获取预算"""
        self.sync.set_budget_state("user1", 1.0, 0.0)
        
        state = self.sync.get_budget_state("user1")
        
        assert state.total_budget == 1.0
        assert state.consumed_budget == 0.0
        assert state.remaining_budget == 1.0
    
    def test_consume_budget(self):
        """测试消耗预算"""
        self.sync.set_budget_state("user1", 1.0, 0.0)
        
        result = self.sync.consume_budget("user1", 0.3)
        
        assert result is True
        state = self.sync.get_budget_state("user1")
        assert state.consumed_budget == 0.3
    
    def test_consume_insufficient_budget(self):
        """测试预算不足"""
        self.sync.set_budget_state("user1", 1.0, 0.9)
        
        result = self.sync.consume_budget("user1", 0.2)
        
        assert result is False
    
    def test_reset_budget(self):
        """测试重置预算"""
        self.sync.set_budget_state("user1", 1.0, 0.5)
        
        result = self.sync.reset_budget("user1")
        
        assert result is True
        state = self.sync.get_budget_state("user1")
        assert state.consumed_budget == 0.0
    
    def test_acquire_and_release_lock(self):
        """测试获取和释放锁"""
        result = self.sync.acquire_lock("user1")
        assert result is True
        
        # 同一实例可以再次获取
        result2 = self.sync.release_lock("user1")
        assert result2 is True
    
    def test_pending_operations(self):
        """测试待同步操作"""
        self.sync.set_budget_state("user1", 1.0, 0.0)
        self.sync.consume_budget("user1", 0.1)
        
        operations = self.sync.get_pending_operations()
        
        assert len(operations) == 1
        assert operations[0].operation_type == "consume"
        assert operations[0].amount == 0.1
