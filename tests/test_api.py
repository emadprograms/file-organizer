import pytest
from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_list_houses_not_found(monkeypatch):
    from pathlib import Path
    class MockConfig:
        areas_root_path = "/does/not/exist/at/all"
    app.state.config = MockConfig()
    response = client.get("/api/houses")
    assert response.status_code == 404

def test_pdf_endpoint_invalid_id():
    class MockConfig:
        areas_root_path = "/tmp"
    app.state.config = MockConfig()
    response = client.get("/api/houses/123/pdf/invalid/id")
    assert response.status_code == 404
