"""
tests/test_risk_scoring.py
Tests for Module 5: Risk Scoring Engine
"""
import pytest
from app.services.risk_scoring import RiskScoringEngine


@pytest.fixture(scope="module")
def risk_engine():
    return RiskScoringEngine()


def test_critical_threat_high_asset_max_score(risk_engine):
    """Critical threat on critical DB should yield a very high score."""
    score = risk_engine.calculate_risk_score(severity="Critical", incident_type="unknown", source_ips=["10.0.0.10"])
    assert score >= 90.0


def test_low_threat_low_asset_low_score(risk_engine):
    """Low threat on default asset should yield a low score."""
    score = risk_engine.calculate_risk_score(severity="Low", incident_type="unknown", source_ips=[])
    assert score <= 30.0


def test_score_capped_at_100(risk_engine):
    """Risk score should never exceed 100."""
    score = risk_engine.calculate_risk_score(severity="Critical", incident_type="account_compromise", source_ips=["10.0.0.10"], alert_count=50)
    assert score <= 100.0


def test_score_is_float(risk_engine):
    """Score should always be a float."""
    score = risk_engine.calculate_risk_score(severity="High", incident_type="api_injection", source_ips=["10.0.0.12"])
    assert isinstance(score, float)


def test_unknown_asset_uses_default(risk_engine):
    """Unknown asset key should fall back to default value."""
    score_unknown = risk_engine.calculate_risk_score(severity="High", source_ips=["192.168.1.1"])
    score_default = risk_engine.calculate_risk_score(severity="High", source_ips=[])
    assert score_unknown == score_default
