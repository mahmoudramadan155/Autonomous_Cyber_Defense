"""
tests/test_log_collector.py
Tests for Module 1: Log Collector Service Unit Tests
"""
import pytest
from app.services.log_collector import LogCollectorService
from app.schemas.log import LogEventCreate
from app.models.log import LogEvent

class _FakeAsyncDB:
    def __init__(self):
        self.added = []
    
    def add(self, obj):
        self.added.append(obj)
        
    def add_all(self, objs):
        self.added.extend(objs)

    async def commit(self):
        pass

    async def refresh(self, obj):
        obj.id = len(self.added)


@pytest.mark.asyncio
async def test_collect_single_log_creates_db_model():
    """Service correctly converts Pydantic schema to SQLAlchemy model and stores it."""
    db = _FakeAsyncDB()
    svc = LogCollectorService(db)
    
    log_in = LogEventCreate(
        source="Linux",
        source_ip="1.1.1.1",
        message="Test sys log"
    )
    
    result = await svc.collect_log(log_in)
    
    assert isinstance(result, LogEvent)
    assert result.source == "Linux"
    assert result.source_ip == "1.1.1.1"
    assert len(db.added) == 1
    assert db.added[0].message == "Test sys log"


@pytest.mark.asyncio
async def test_bulk_collect_logs_creates_multiple():
    """Service correctly processes and saves lists of logs."""
    db = _FakeAsyncDB()
    svc = LogCollectorService(db)
    
    logs_in = [
        LogEventCreate(source="Windows", message="Fail"),
        LogEventCreate(source="Linux", message="Success"),
    ]
    
    results = await svc.bulk_collect_logs(logs_in)
    
    assert len(results) == 2
    assert len(db.added) == 2
    assert db.added[0].source == "Windows"
    assert db.added[1].source == "Linux"
