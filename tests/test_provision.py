from fastapi.testclient import TestClient

from provision.main import app

client = TestClient(app)


def test_render_is_not_an_apply():
    body = client.post("/stacks", json={"name": "billing", "environment": "dev"}).json()
    assert body["applied"] is False
    assert 'name        = "billing"' in body["files"]["main.tf"]
    assert client.post("/stacks", json={"name": "billing", "environment": "prod"}).status_code == 422
