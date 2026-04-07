"""API 集成测试

使用 FastAPI TestClient，不走真实网络。
"""

import pytest
from src.data.database import reset_db


@pytest.fixture(autouse=True)
async def fresh_db():
    """每个测试前重置数据库到干净的内存状态"""
    await reset_db()


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    from fastapi.testclient import TestClient
    from src.api.main import create_app
    app = create_app()
    return TestClient(app)


AUTH_HEADERS = {"Authorization": "Bearer test-token"}


class TestHealthEndpoint:
    def test_root(self, client):
        res = client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Council"

    def test_health(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestAgentsEndpoint:
    def test_list_agents(self, client):
        res = client.get("/api/agents", headers=AUTH_HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert "agents" in data
        names = [a["name"] for a in data["agents"]]
        assert "promoter" in names
        assert "perspectivist" in names


class TestAuth:
    def test_no_auth(self, client):
        res = client.get("/api/agents")
        assert res.status_code == 401

    def test_wrong_auth(self, client):
        res = client.get("/api/agents", headers={"Authorization": "Bearer wrong"})
        assert res.status_code == 401

    def test_valid_auth(self, client):
        res = client.get("/api/agents", headers=AUTH_HEADERS)
        assert res.status_code == 200


class TestConversationEndpoint:
    def test_create_conversation(self, client):
        res = client.post(
            "/api/conversations",
            json={"title": "测试对话"},
            headers={**AUTH_HEADERS, "Content-Type": "application/json"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        assert data["title"] == "测试对话"

    def test_list_conversations(self, client):
        # 先创建一个
        client.post(
            "/api/conversations",
            json={"title": "列表测试"},
            headers={**AUTH_HEADERS, "Content-Type": "application/json"},
        )
        res = client.get("/api/conversations", headers=AUTH_HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
