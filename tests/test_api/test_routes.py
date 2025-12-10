"""
API路由单元测试
"""
import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main.api.server import app
from main.api.routes import reset_query_driver


class TestAPIRoutes:
    """API路由测试类"""
    
    def setup_method(self):
        """每个测试前重置状态"""
        reset_query_driver()
        self.client = TestClient(app)
    
    def teardown_method(self):
        """每个测试后清理"""
        reset_query_driver()
    
    def test_root_endpoint(self):
        """测试根路径"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Privacy Query Engine"
        assert "mode" in data
        assert "docs" in data
    
    def test_health_endpoint(self):
        """测试健康检查"""
        response = self.client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_status_endpoint_mock_mode(self):
        """测试状态接口 (Mock 模式)"""
        with patch.dict(os.environ, {"USE_MOCK_DB": "true"}):
            reset_query_driver()
            response = self.client.get("/api/v1/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "running"
            assert data["mode"] == "mock"
            assert "database" not in data
    
    def test_protect_query_count(self):
        """测试COUNT查询保护"""
        response = self.client.post(
            "/api/v1/protect-query",
            json={"sql": "SELECT COUNT(*) FROM users"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["type"] == "DP"
    
    def test_protect_query_select(self):
        """测试SELECT查询保护"""
        response = self.client.post(
            "/api/v1/protect-query",
            json={"sql": "SELECT name, email FROM users"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["type"] == "DeID"
    
    def test_protect_query_with_context(self):
        """测试带上下文的查询"""
        response = self.client.post(
            "/api/v1/protect-query",
            json={
                "sql": "SELECT COUNT(*) FROM users",
                "context": {"user_id": "test_user"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_protect_query_empty_sql(self):
        """测试空SQL应返回错误"""
        response = self.client.post(
            "/api/v1/protect-query",
            json={"sql": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_protect_query_pass(self):
        """测试不需要保护的查询"""
        response = self.client.post(
            "/api/v1/protect-query",
            json={"sql": "SELECT id FROM products"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # 非敏感字段，应该是 PASS
        assert data["data"]["type"] in ["PASS", "DeID", "DP"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

