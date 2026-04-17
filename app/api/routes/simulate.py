from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.log import LogEventCreate
from app.services.log_collector import LogCollectorService
from app.services.threat_detection import ThreatDetectionService
from app.services.correlation_engine import CorrelationEngine
from faker import Faker
import random
import logging
import asyncio

router = APIRouter()
fake = Faker()

SQLI_PAYLOADS = [
    "' OR '1'='1", "UNION SELECT * FROM users--", "'; DROP TABLE logs--",
    "1' AND 1=1--", "admin'--"
]
XSS_PAYLOADS = [
    "<script>alert(1)</script>", "javascript:alert(1)",
    "<img src=x onerror=alert(1)>", "<svg onload=alert(1)>"
]


def make_brute_force_log(source_ip: str, attempt: int) -> LogEventCreate:
    return LogEventCreate(
        source="Nginx",
        source_ip=source_ip,
        method="POST",
        path="/api/v1/login",
        status_code=401,
        message=f"failed login attempt #{attempt}",
        user_agent=fake.user_agent(),
    )


def make_sqli_log(source_ip: str) -> LogEventCreate:
    return LogEventCreate(
        source="API",
        source_ip=source_ip,
        method="GET",
        path=f"/api/v1/users?id={random.choice(SQLI_PAYLOADS)}",
        status_code=200,
        payload=random.choice(SQLI_PAYLOADS),
        user_agent=fake.user_agent(),
    )


def make_xss_log(source_ip: str) -> LogEventCreate:
    return LogEventCreate(
        source="API",
        source_ip=source_ip,
        method="POST",
        path="/api/v1/comments",
        status_code=200,
        payload=random.choice(XSS_PAYLOADS),
        user_agent=fake.user_agent(),
    )


def make_port_scan_log(source_ip: str, port: int) -> LogEventCreate:
    return LogEventCreate(
        source="FortiGate",
        source_ip=source_ip,
        destination_ip="10.0.0.1",
        method="TCP",
        path=f"port:{port}",
        status_code=0,
        message=f"Port scan attempt on port {port}",
    )


def make_ddos_log(source_ip: str, seq: int) -> LogEventCreate:
    return LogEventCreate(
        source="Nginx",
        source_ip=source_ip,
        method="GET",
        path="/",
        status_code=200,
        message=f"DDoS flood packet #{seq}",
        user_agent=fake.user_agent(),
    )


async def _run_simulation(attack_type: str):
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        collector = LogCollectorService(db)
        detector = ThreatDetectionService(db)
        correlator = CorrelationEngine(db)
        source_ip = fake.ipv4_private()

        if attack_type == "brute_force":
            for i in range(5):
                log = await collector.collect_log(make_brute_force_log(source_ip, i + 1))
                alert = await detector.detect_threats(log)
                if alert:
                    await correlator.correlate_alerts(alert)

        elif attack_type == "sqli":
            for _ in range(3):
                log = await collector.collect_log(make_sqli_log(source_ip))
                alert = await detector.detect_threats(log)
                if alert:
                    await correlator.correlate_alerts(alert)

        elif attack_type == "xss":
            for _ in range(3):
                log = await collector.collect_log(make_xss_log(source_ip))
                alert = await detector.detect_threats(log)
                if alert:
                    await correlator.correlate_alerts(alert)

        elif attack_type == "port_scan":
            for port in [22, 23, 80, 443, 3306, 5432, 8080]:
                log = await collector.collect_log(make_port_scan_log(source_ip, port))
                alert = await detector.detect_threats(log)
                if alert:
                    await correlator.correlate_alerts(alert)

        elif attack_type == "ddos":
            for i in range(20):
                log = await collector.collect_log(make_ddos_log(source_ip, i + 1))


@router.post("/simulate/{attack_type}", status_code=202)
async def simulate_attack(attack_type: str, background_tasks: BackgroundTasks):
    """
    Red Team simulation. attack_type: brute_force | sqli | xss | port_scan | ddos
    """
    supported = ["brute_force", "sqli", "xss", "port_scan", "ddos"]
    if attack_type not in supported:
        from fastapi import HTTPException
        logging.error(f"Red Team simulation triggered with INVALID type: {attack_type}")
        raise HTTPException(status_code=400, detail=f"Unknown attack type. Use: {supported}")

    logging.warning(f"*** RED TEAM MODE ACTIVATED: Firing '{attack_type}' payload sequence! ***")
    background_tasks.add_task(_run_simulation, attack_type)
    return {"status": "Simulation started", "attack_type": attack_type}
