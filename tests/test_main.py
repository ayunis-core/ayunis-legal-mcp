"""
Tests for main application endpoints
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Legal MCP API"}


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_info():
    """Test info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "admin_email" in data
    assert "version" in data


def test_read_items():
    """Test items list endpoint"""
    response = client.get("/items/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_users():
    """Test users list endpoint"""
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

