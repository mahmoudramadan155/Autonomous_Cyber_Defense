"""
Enhanced Correlation Engine
Groups related alerts into confirmed incidents using 6 rules.
Applies a 2-minute sliding time window per source IP.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models.alert import Alert
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate
from app.services.risk_scoring import RiskScoringEngine

logger = logging.getLogger(__name__)

# In-memory cooldown: prevent re-firing the same incident within 60s per IP
_incident_cooldown: dict[str, float] = {}
_risk_engine = RiskScoringEngine()


class CorrelationEngine:
    """
    Correlates alerts into incidents using 6 pattern rules.
    """

    WINDOW_MINUTES = 2

    def __init__(self, db: AsyncSession):
        self.db = db

    async def correlate_alerts(self, new_alert: Alert) -> Optional[Incident]:
        """
        Check recent alerts for the same IP and apply correlation rules.
        """
        ip = new_alert.source_ip or "unknown"
        now = datetime.now(timezone.utc)
        time_window = now - timedelta(minutes=self.WINDOW_MINUTES)

        # Load recent alerts from DB (same IP, last 2 minutes, not yet correlated)
        query = (
            select(Alert)
            .where(
                Alert.source_ip == ip,
                Alert.tenant_id == (new_alert.tenant_id or "default"),
                Alert.timestamp >= time_window,
                Alert.id != new_alert.id,
            )
            .order_by(desc(Alert.timestamp))
        )
        result = await self.db.execute(query)
        recent_alerts = result.scalars().all()
        all_alerts = list(recent_alerts) + [new_alert]

        if len(all_alerts) < 2:
            return None

        # Cooldown check
        import time
        last = _incident_cooldown.get(ip, 0)
        if time.time() - last < 60:
            return None

        incident_data = self._apply_rules(ip, all_alerts)
        if not incident_data:
            return None

        # Risk scoring
        risk_score = _risk_engine.calculate_risk_score(
            incident_type=incident_data.get("incident_type", "unknown"),
            severity=incident_data.get("severity", "Medium"),
            alert_count=len(all_alerts),
        )
        risk_level = _risk_engine.risk_level(risk_score)

        logger.critical(
            f"🔴 INCIDENT: {incident_data['title']} | {incident_data['severity']} "
            f"| risk={risk_score} | ips=[{ip}]"
        )

        incident = Incident(
            title=incident_data["title"],
            incident_type=incident_data["incident_type"],
            severity=incident_data["severity"],
            risk_score=risk_score,
            risk_level=risk_level,
            source_ips=[ip],
            description=incident_data["description"],
            root_cause=incident_data.get("root_cause"),
            recommendations=incident_data.get("recommendations"),
            requires_immediate_action=(risk_score >= 80),
            tenant_id=new_alert.tenant_id or "default",
        )
        self.db.add(incident)
        await self.db.flush()

        # Link all related alerts
        for alert in all_alerts:
            alert.is_correlated = True
            alert.incident_id = incident.id

        await self.db.commit()
        await self.db.refresh(incident)

        # Update cooldown
        import time
        _incident_cooldown[ip] = time.time()

        return incident

    def _apply_rules(self, ip: str, alerts: list[Alert]) -> Optional[dict]:
        """Apply all 6 correlation rules. Returns first match."""
        threats = {a.threat_type for a in alerts}

        # ── Rule 1: Account Compromise ──────────────────────────────────
        has_brute = "Brute Force" in threats
        has_fail = "Failed Login" in threats
        has_sqli = "SQL Injection" in threats
        has_xss = "XSS Attack" in threats
        has_ddos = "DDoS" in threats
        has_api = "API Abuse" in threats

        if has_brute and len(alerts) >= 3:
            return {
                "title": f"Sustained Brute Force Attack from {ip}",
                "incident_type": "brute_force",
                "severity": "High",
                "description": f"Multiple brute force alerts detected from {ip} within 2 minutes.",
                "root_cause": "Automated credential stuffing or dictionary attack.",
                "recommendations": "Block the source IP, enforce MFA, and review account lockout policies.",
            }

        # ── Rule 2: Web Application Attack ─────────────────────────────
        if has_sqli and has_xss:
            return {
                "title": f"Web Application Attack from {ip}",
                "incident_type": "web_attack",
                "severity": "High",
                "description": f"Combined SQLi and XSS attacks from {ip}.",
                "root_cause": "Automated web application scanner or exploit framework.",
                "recommendations": "Review WAF rules, sanitize inputs, and block the attacking IP.",
            }

        # ── Rule 3: SQLi + API Abuse → API Injection ───────────────────
        if has_sqli and has_api:
            return {
                "title": f"API Injection Attack from {ip}",
                "incident_type": "api_injection",
                "severity": "Critical",
                "description": f"SQL injection combined with API abuse from {ip}.",
                "root_cause": "Targeted API exploitation using injection payloads.",
                "recommendations": "Immediately block IP, rotate API keys, review all API endpoints.",
            }

        # ── Rule 4: DDoS Campaign ──────────────────────────────────────
        ddos_count = sum(1 for a in alerts if a.threat_type == "DDoS")
        if ddos_count >= 2:
            return {
                "title": f"Distributed Denial of Service from {ip}",
                "incident_type": "ddos",
                "severity": "Critical",
                "description": f"Multiple DDoS alert signals from {ip}.",
                "root_cause": "Volumetric DDoS attack targeting network resources.",
                "recommendations": "Rate-limit source IP, activate upstream scrubbing, alert NOC.",
            }

        # ── Rule 5: Reconnaissance → Attack ────────────────────────────
        has_port_scan = "Port Scan" in threats
        if has_port_scan and (has_sqli or has_brute or has_ddos):
            return {
                "title": f"Reconnaissance Followed by Attack from {ip}",
                "incident_type": "recon_attack",
                "severity": "High",
                "description": f"Port scan followed by active exploit from {ip}.",
                "root_cause": "Attacker mapped network then launched targeted exploit.",
                "recommendations": "Block IP, review firewall rules, check for lateral movement.",
            }

        # ── Rule 6: Suspicious UA + Any Attack ─────────────────────────
        has_sus_ua = "Suspicious User Agent" in threats
        if has_sus_ua and len(alerts) >= 3:
            return {
                "title": f"Automated Attack Tool Detected from {ip}",
                "incident_type": "automated_attack",
                "severity": "Medium",
                "description": f"Known attack tool combined with suspicious activity from {ip}.",
                "root_cause": "Automated scanning or exploitation tool.",
                "recommendations": "Block IP, review logs for exfiltration attempts.",
            }

        # ── Catch-all: 5+ alerts from same IP ──────────────────────────
        if len(alerts) >= 5:
            return {
                "title": f"Coordinated Attack from {ip}",
                "incident_type": "coordinated_attack",
                "severity": "High",
                "description": f"Multiple ({len(alerts)}) security alerts from {ip} within 2 minutes.",
                "root_cause": "Coordinated or automated attack campaign.",
                "recommendations": "Block the source IP and investigate all related logs.",
            }

        return None
