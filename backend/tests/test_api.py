import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "the spirits are listening"
    assert "version" in data


def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "the spirits are listening"


def test_seance_scan_invalid_url():
    response = client.post("/api/seance/scan", json={"repo_url": "invalid-url"})
    assert response.status_code in (400, 422)


def test_seance_scan_demo_repo():
    # flask-cache preset is guaranteed to succeed via demo snapshot even without GitHub token
    response = client.post(
        "/api/seance/scan",
        json={"repo_url": "https://github.com/mitsuhiko/flask-cache"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["repo_name"] == "flask-cache"
    assert data["total_files_scanned"] > 0
    assert "haunting_reports" in data
    assert len(data["haunting_reports"]) > 0


def test_seance_stream_demo_repo():
    # Test that the SSE endpoint begins streaming events
    response = client.get(
        "/api/seance/stream?repo_url=https://github.com/mitsuhiko/flask-cache"
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    content = response.text
    assert "data:" in content
    assert "reaper" in content
