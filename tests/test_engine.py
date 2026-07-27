import pytest
import yaml
from site_decision.engine import evaluate
from site_decision.models import CheckStatus

@pytest.fixture
def default_config():
    with open("site_decision/config/default_operator.yaml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def operator_b_config():
    with open("site_decision/config/operator_b.yaml") as f:
        return yaml.safe_load(f)

def test_rnp_failure_blocks_immediately(default_config):
    # RNP fails, so it should short-circuit and REJECT, and not evaluate others
    site = {
        "site_id": "SITE-1",
        "site_type": "rooftop",
        "current_load_pct": 50,      # < 80, fails RNP
        "spectrum_available": True,
        "backhaul_capacity_mbps": 100, # Missing this would be NEEDS_REVIEW, but short circuit avoids it
    }
    decision = evaluate(site, default_config)
    assert decision.outcome == "REJECTED"
    assert len(decision.check_results) == 1
    assert decision.check_results[0].check_name == "rnp"

def test_transmission_failure_degrading(default_config):
    # RNP passes, Transmission fails (DEGRADING), Power passes -> APPROVED with prerequisite
    site = {
        "site_id": "SITE-2",
        "site_type": "rooftop",
        "current_load_pct": 90,
        "spectrum_available": True,
        "backhaul_capacity_mbps": 100,
        "backhaul_required_mbps": 200, # Fails transmission
        "power_headroom_kw": 5.0,      # Passes power
    }
    decision = evaluate(site, default_config)
    assert decision.outcome == "APPROVED"
    assert len(decision.prerequisites) == 1
    assert "transmission" in decision.prerequisites[0].lower()

def test_missing_data_needs_review(default_config):
    # Missing power headroom
    site = {
        "site_id": "SITE-3",
        "site_type": "rooftop",
        "current_load_pct": 90,
        "spectrum_available": True,
        "backhaul_capacity_mbps": 500,
        "backhaul_required_mbps": 400,
        # power_headroom_kw is missing
    }
    decision = evaluate(site, default_config)
    assert decision.outcome == "NEEDS_REVIEW"
    assert len(decision.check_results) == 3
    assert any(r.status == CheckStatus.NEEDS_REVIEW and r.check_name == "power" for r in decision.check_results)

def test_cross_operator_configs(default_config, operator_b_config):
    site = {
        "site_id": "SITE-4",
        "site_type": "rooftop",
        "current_load_pct": 78,
        "spectrum_available": True,
        "backhaul_capacity_mbps": 500,
        "backhaul_required_mbps": 400,
        "power_headroom_kw": 5.0,
    }
    # default config requires 80% load for RNP
    decision_a = evaluate(site, default_config)
    assert decision_a.outcome == "REJECTED"

    # operator B config requires 75% load for RNP
    decision_b = evaluate(site, operator_b_config)
    assert decision_b.outcome == "APPROVED"

def test_forward_compatibility(default_config):
    # Extra field should not break anything
    site = {
        "site_id": "SITE-5",
        "site_type": "rooftop",
        "current_load_pct": 90,
        "spectrum_available": True,
        "backhaul_capacity_mbps": 500,
        "backhaul_required_mbps": 400,
        "power_headroom_kw": 5.0,
        "unknown_new_field": "some_value"
    }
    decision = evaluate(site, default_config)
    assert decision.outcome == "APPROVED"

def test_transmission_zero_required_bandwidth(default_config):
    site = {
        "site_id": "SITE-6",
        "site_type": "rooftop",
        "current_load_pct": 90,
        "spectrum_available": True,
        "backhaul_capacity_mbps": 500,
        "backhaul_required_mbps": 0,
        "power_headroom_kw": 5.0,
    }
    decision = evaluate(site, default_config)
    assert decision.outcome == "NEEDS_REVIEW"
    assert any(r.check_name == "transmission" and r.status == CheckStatus.NEEDS_REVIEW for r in decision.check_results)

def test_power_required_kw_exceeds_headroom(default_config):
    site = {
        "site_id": "SITE-7",
        "site_type": "rooftop",
        "current_load_pct": 90,
        "spectrum_available": True,
        "backhaul_capacity_mbps": 500,
        "backhaul_required_mbps": 400,
        "power_headroom_kw": 3.0,
        "power_required_kw": 5.0, # Required exceeds headroom
    }
    decision = evaluate(site, default_config)
    assert decision.outcome == "REJECTED"
    assert any(r.check_name == "power" and r.status == CheckStatus.FAIL for r in decision.check_results)

