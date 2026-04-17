"""
tests/test_simulation.py
Tests for Module 7: Red Team / Attack Simulation
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_simulate_brute_force(client: AsyncClient):
    """Red team brute-force simulation should return 202."""
    response = await client.post("/api/v1/red-team/simulate/brute_force")
    assert response.status_code == 202
    assert response.json()["attack_type"] == "brute_force"


@pytest.mark.asyncio
async def test_simulate_sqli(client: AsyncClient):
    """Red team SQL injection simulation should return 202."""
    response = await client.post("/api/v1/red-team/simulate/sqli")
    assert response.status_code == 202
    assert response.json()["attack_type"] == "sqli"


@pytest.mark.asyncio
async def test_simulate_xss(client: AsyncClient):
    """Red team XSS simulation should return 202."""
    response = await client.post("/api/v1/red-team/simulate/xss")
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_simulate_port_scan(client: AsyncClient):
    response = await client.post("/api/v1/red-team/simulate/port_scan")
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_simulate_ddos(client: AsyncClient):
    response = await client.post("/api/v1/red-team/simulate/ddos")
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_simulate_unknown_type(client: AsyncClient):
    """Unknown attack type should return 400."""
    response = await client.post("/api/v1/red-team/simulate/unknown_hack")
    assert response.status_code == 400
