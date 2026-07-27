import os
import pytest
from fastapi.testclient import TestClient

# Ensure config path is set for the API tests
os.environ["SITE_CONFIG_PATH"] = "site_decision/config/default_operator.yaml"

from site_decision.api import app
from site_decision.engine import evaluate
import yaml

client = TestClient(app)

def test_api_evaluate_matches_engine():
    site_payload = {
        "site_id": "SITE-1042",
        "site_type": "rooftop",
        "current_load_pct": 92,
        "spectrum_available": True,
        "backhaul_capacity_mbps": 450,
        "backhaul_required_mbps": 600,
        "power_headroom_kw": 3.2,
        "power_required_kw": 2.8
    }

    # API call
    response = client.post("/evaluate", json=site_payload)
    assert response.status_code == 200
    api_decision = response.json()

    # Direct engine call
    with open("site_decision/config/default_operator.yaml") as f:
        config = yaml.safe_load(f)
    
    engine_decision = evaluate(site_payload, config)
    
    # Assert they match
    assert api_decision["outcome"] == engine_decision.outcome
    assert api_decision["site_id"] == engine_decision.site_id
    # Assert prerequisites match
    assert len(api_decision["prerequisites"]) == len(engine_decision.prerequisites)

def test_api_unknown_site_type():
    site_payload = {
        "site_id": "SITE-1043",
        "site_type": "unknown_type",
    }
    response = client.post("/evaluate", json=site_payload)
    assert response.status_code == 400
    assert "Unknown site_type" in response.json()["detail"]
