"""
API路由单元测试
"""
import pytest
from fastapi.testclient import TestClient
from main.api.server import app


class TestAPIRoutes:
    """API路由测试类"""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """测试根路径"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Privacy Query Engine"
    
    def test_health_endpoint(self):
        """测试健康检查"""
        response = self.client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
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
    
    def test_protect_query_empty_sql(self):
        """测试空SQL应返回错误"""
        response = self.client.post(
            "/api/v1/protect-query",
            json={"sql": ""}
        )
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

