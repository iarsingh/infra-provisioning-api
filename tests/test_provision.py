from fastapi.testclient import TestClient

from provision.main import app

client = TestClient(app)

GOOD = {"name": "billing", "environment": "dev", "region": "us-central1", "size": "small", "team": "payments", "cost_center": "cc_104"}


def stack(**overrides):
    return client.post("/stacks", json={**GOOD, **overrides})


def test_render_is_not_an_apply():
    body = stack().json()
    assert body["applied"] is False
    assert 'name         = "billing"' in body["files"]["terraform.tfvars"]
    assert "var.name" in body["files"]["main.tf"]
    assert stack(environment="prod").status_code == 422


def test_estimate_follows_the_size():
    body = stack(size="medium").json()
    assert body["estimate"] == {"machine_type": "e2-standard-2", "monthly_usd": 49}


def test_dev_is_capped_at_medium():
    response = stack(size="large")
    assert response.status_code == 422
    assert "capped at medium" in response.json()["detail"]
    assert stack(environment="staging", size="large").status_code == 200


def test_quote_in_name_cannot_inject_hcl():
    response = stack(name='billing"\n  source = "evil')
    assert response.status_code == 422


def test_unknown_region_is_refused():
    assert stack(region="us-east1").status_code == 422


def test_labels_are_required():
    assert "team label is required" in stack(team="").json()["detail"]
    assert "cost_center label is required" in stack(cost_center="CC 104").json()["detail"]


def test_labels_are_rendered():
    tfvars = stack().json()["files"]["terraform.tfvars"]
    assert 'team        = "payments"' in tfvars
    assert 'managed_by  = "provisioning-api"' in tfvars


def test_options_list_regions_and_caps():
    body = client.get("/options").json()
    assert "asia-south1" in body["regions"]
    assert body["size_cap"]["dev"] == "medium"
