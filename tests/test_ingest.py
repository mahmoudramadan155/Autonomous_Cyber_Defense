"""
tests/test_ingest.py
Tests for Module 1: Log Collection Engine
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Platform health endpoint should return 200."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_single_log(client: AsyncClient):
    """POST /ingest/logs should accept a valid log and return 202."""
    payload = {
        "source": "Nginx",
        "source_ip": "10.0.0.1",
        "method": "GET",
        "path": "/index.html",
        "status_code": 200,
        "message": "Normal request"
    }
    response = await client.post("/api/v1/ingest/logs", json=payload)
    assert response.status_code == 202
    assert response.json()["status"] == "Processing initiated"


@pytest.mark.asyncio
async def test_ingest_bulk_logs(client: AsyncClient):
    """POST /ingest/logs/bulk should accept multiple logs."""
    logs = [
        {"source": "Linux", "source_ip": "192.168.1.1", "message": "sudo command run"},
        {"source": "Apache", "source_ip": "192.168.1.2", "method": "POST", "path": "/login", "status_code": 401},
        {"source": "FortiGate", "source_ip": "10.10.10.1", "destination_ip": "10.0.0.5", "message": "Firewall rule triggered"},
    ]
    response = await client.post("/api/v1/ingest/logs/bulk", json=logs)
    assert response.status_code == 202
    assert "3 logs" in response.json()["status"]


@pytest.mark.asyncio
async def test_ingest_missing_source_returns_error(client: AsyncClient):
    """Log without required 'source' field should return 422."""
    response = await client.post("/api/v1/ingest/logs", json={"source_ip": "1.1.1.1"})
    assert response.status_code == 422
