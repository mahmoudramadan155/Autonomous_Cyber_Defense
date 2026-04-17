"""
tests/test_correlation_engine.py
Tests for Module 4: Correlation Engine Logic Unit Tests
"""
import pytest
from datetime import datetime
from app.services.correlation_engine import CorrelationEngine
from app.models.alert import Alert

class _FakeAsyncScalarResult:
    def __init__(self, data):
        self.data = data
    def scalars(self):
        class _Inner:
            def all(inner_self): return self.data
            def first(inner_self): return self.data[0] if self.data else None
        return _Inner()

class _FakeAsyncSessionForCorrelation:
    def __init__(self, existing_alerts=None):
        self.existing_alerts = existing_alerts or []
        self.added = []
        self.flushed = False
        
    async def execute(self, query):
        return _FakeAsyncScalarResult(self.existing_alerts)

    def add(self, obj):
        obj.id = 999
        self.added.append(obj)

    async def flush(self):
        self.flushed = True
        
    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

@pytest.mark.asyncio
async def test_correlation_triggers_with_enough_history():
    """If there are 2 existing recent alerts, a 3rd alert triggers an Incident."""
    # Mocking 2 existing un-correlated alerts from the same IP
    existing = [
        Alert(id=1, source_ip="10.0.0.5", is_correlated=False),
        Alert(id=2, source_ip="10.0.0.5", is_correlated=False),
        Alert(id=11, source_ip="10.0.0.5", is_correlated=False),
        Alert(id=12, source_ip="10.0.0.5", is_correlated=False)
    ]
    db = _FakeAsyncSessionForCorrelation(existing_alerts=existing)
    
    svc = CorrelationEngine(db)
    new_alert = Alert(id=3, source_ip="10.0.0.5", is_correlated=False, tenant_id="tenant-A")
    
    await svc.correlate_alerts(new_alert)
    
    # Assert incident was created
    assert len(db.added) == 1
    incident = db.added[0]
    assert incident.title == "Coordinated Attack from 10.0.0.5"
    assert incident.tenant_id == "tenant-A"
    assert incident.severity == "High"
    
    # Assert alerts were marked correlated
    assert new_alert.is_correlated is True
    assert new_alert.incident_id == 999
    for alert in existing:
        assert alert.is_correlated is True
        assert alert.incident_id == 999

@pytest.mark.asyncio
async def test_correlation_ignores_isolated_alerts():
    """If there are less than 2 previous alerts, no incident occurs."""
    existing = [Alert(id=1, source_ip="8.8.8.8", is_correlated=False)]
    db = _FakeAsyncSessionForCorrelation(existing_alerts=existing)
    
    svc = CorrelationEngine(db)
    new_alert = Alert(id=2, source_ip="8.8.8.8", is_correlated=False)
    
    await svc.correlate_alerts(new_alert)
    
    # Assert no incident created
    assert len(db.added) == 0
    assert new_alert.is_correlated is False
