"""
tests/test_threat_detection.py
Tests for Module 2: Real-Time Threat Detection Engine
"""
import pytest
from app.services.threat_detection import ThreatDetectionService
from app.models.log import LogEvent


class _FakeDB:
    """Minimal async DB stub that captures added objects."""
    def __init__(self):
        self._added = []
        self._id_counter = 1

    def add(self, obj):
        obj.id = self._id_counter
        self._id_counter += 1
        self._added.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


def make_log(**kwargs) -> LogEvent:
    log = LogEvent()
    log.id = 1
    log.source_ip = kwargs.get("source_ip", "1.2.3.4")
    log.path = kwargs.get("path", "/")
    log.payload = kwargs.get("payload", None)
    log.message = kwargs.get("message", None)
    return log


@pytest.mark.asyncio
async def test_detects_sql_injection():
    """SQLi pattern in path should generate a High alert."""
    db = _FakeDB()
    svc = ThreatDetectionService(db)
    log = make_log(path="/users?id=' OR '1'='1")
    alert = await svc.detect_threats(log)
    assert alert is not None
    assert alert.threat_type == "SQL Injection"
    assert alert.severity == "High"
    assert alert.confidence >= 0.90


@pytest.mark.asyncio
async def test_detects_sql_injection_in_payload():
    """SQLi pattern in payload body should also be caught."""
    db = _FakeDB()
    svc = ThreatDetectionService(db)
    log = make_log(payload="UNION SELECT * FROM users--")
    alert = await svc.detect_threats(log)
    assert alert is not None
    assert alert.threat_type == "SQL Injection"


@pytest.mark.asyncio
async def test_detects_xss():
    """XSS payload in body should produce a Medium alert."""
    db = _FakeDB()
    svc = ThreatDetectionService(db)
    log = make_log(payload="<script>alert(1)</script>")
    alert = await svc.detect_threats(log)
    assert alert is not None
    assert alert.threat_type == "XSS Attack"
    assert alert.severity == "Medium"


@pytest.mark.asyncio
async def test_detects_failed_login():
    """'failed login' in message should produce a Low alert."""
    db = _FakeDB()
    svc = ThreatDetectionService(db)
    log = make_log(message="Failed login attempt from admin")
    alert = await svc.detect_threats(log)
    assert alert is not None
    assert alert.threat_type == "Failed Login"
    assert alert.severity == "Low"


@pytest.mark.asyncio
async def test_no_threat_on_normal_request():
    """Normal traffic should produce no alert."""
    db = _FakeDB()
    svc = ThreatDetectionService(db)
    log = make_log(path="/api/v1/items", message="Normal page load")
    alert = await svc.detect_threats(log)
    assert alert is None
