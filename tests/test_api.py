"""Basic API tests"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Synapse"


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_completions():
    """Test chat completions endpoint"""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "synapse",
            "messages": [{"role": "user", "content": "Hello"}]
        },
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0


def test_list_models():
    """Test models endpoint"""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0