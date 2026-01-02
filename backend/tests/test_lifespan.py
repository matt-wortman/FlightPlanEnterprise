from fastapi.testclient import TestClient

from app.main import app


def test_lifespan_loads_plugins():
    with TestClient(app) as client:
        resp = client.get("/api/v1/specialties")
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()]
        assert "cardiac" in names
