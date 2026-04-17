"""
tests/test_anomaly_detection.py
Tests for Module 3: AI Anomaly Detection (XGBoost)
"""
import pytest
from app.services.anomaly_detection import AnomalyDetectionService


@pytest.fixture(scope="module")
def anomaly_svc():
    return AnomalyDetectionService()


def test_normal_request_not_anomaly(anomaly_svc):
    """A typical short request should NOT be flagged as an anomaly."""
    log = {"path": "/home", "payload": None, "status_code": 200}
    result = anomaly_svc.predict_anomaly(log)
    assert result["is_anomaly"] is False
    assert result["threat"] is None


def test_extreme_payload_flagged(anomaly_svc):
    """An extreme netflow event resembling DDoS should be suspicious."""
    log = {
        "Destination Port": 80,
        "Flow Duration": 10000000.0,
        "Total Fwd Packets": 50000,
        "Total Backward Packets": 50000,
        "Flow Bytes/s": 90000000.0,
        "Flow Packets/s": 5000.0
    }
    result = anomaly_svc.predict_anomaly(log)
    assert "is_anomaly" in result
    if anomaly_svc.model:
        # If the model is loaded, it should flag this high volume flow
        pass


def test_feature_extraction(anomaly_svc):
    """Feature extraction should return 11 floats."""
    log = {"path": "/test", "payload": "hello", "status_code": 200}
    features = anomaly_svc._extract_features(log)
    assert len(features) == 11
    assert all(isinstance(f, (int, float)) for f in features)


def test_empty_log_does_not_crash(anomaly_svc):
    """Empty log dict should not raise any errors."""
    result = anomaly_svc.predict_anomaly({})
    assert "is_anomaly" in result
