"""
Enhanced Rule-Based Threat Detection Service
Implements 7 detection rules with MITRE ATT&CK mappings and sliding window counters.
"""
import re
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import LogEvent
from app.models.alert import Alert
from app.schemas.alert import AlertCreate

logger = logging.getLogger(__name__)


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


# ─────────────────────────────────────────────────────────
# STATEFUL SLIDING WINDOW COUNTERS (in-memory, per-process)
# ─────────────────────────────────────────────────────────

_login_fail_tracker: dict = defaultdict(lambda: deque(maxlen=200))
_http_req_tracker: dict = defaultdict(lambda: deque(maxlen=500))
_api_req_tracker: dict = defaultdict(lambda: deque(maxlen=200))
_port_scan_tracker: dict = defaultdict(lambda: deque(maxlen=200))

# ─────────────────────────────────────────────────────────
# COMPILED REGEX PATTERNS
# ─────────────────────────────────────────────────────────

SQLI_PATTERNS = [
    re.compile(r"(union\s+(all\s+)?select)", re.IGNORECASE),
    re.compile(r"(select\s+.+\s+from)", re.IGNORECASE),
    re.compile(r"(insert\s+into|drop\s+table|delete\s+from)", re.IGNORECASE),
    re.compile(r"(sleep\s*\(\d+\)|benchmark\s*\()", re.IGNORECASE),
    re.compile(r"('\\s*(or|and)\\s*'?\\d+'?\\s*=\\s*'?\\d+'?)", re.IGNORECASE),
    re.compile(r"(' OR '1'='1|' or 1=1|OR 1=1--)", re.IGNORECASE),
    re.compile(r"(--|;--|\\')", re.IGNORECASE),
]

XSS_PATTERNS = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on(load|click|error|mouseover)\s*=", re.IGNORECASE),
    re.compile(r"<iframe[^>]*>", re.IGNORECASE),
]

SUSPICIOUS_UA_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"sqlmap", r"nikto", r"nmap", r"hydra", r"metasploit",
        r"burpsuite", r"masscan", r"zgrab", r"dirbuster",
    ]
]


class ThreatDetectionService:
    """
    Multi-rule threat detection engine with MITRE ATT&CK mappings.
    Rules: Brute Force, SQLi, XSS, Port Scan, DDoS, API Abuse, Suspicious UA
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_threats(self, log_event: LogEvent) -> Optional[Alert]:
        """
        Run all detection rules in priority order.
        Returns the first (highest confidence) alert found.
        """
        alert_data = (
            self._check_sqli(log_event)
            or self._check_xss(log_event)
            or self._check_suspicious_ua(log_event)
            or self._check_brute_force(log_event)
            or self._check_ddos(log_event)
            or self._check_api_abuse(log_event)
            or self._check_port_scan(log_event)
            or self._check_failed_login(log_event)
        )

        if alert_data:
            logger.warning(
                f"🚨 ALERT: {alert_data['threat_type']} | {alert_data['severity']} "
                f"| {log_event.source_ip} | conf={alert_data['confidence']:.2f}"
            )
            alert = Alert(**alert_data)
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)
            return alert

        return None

    # ──────────────────────────────────────────────────────
    # RULE 1: SQL Injection
    # ──────────────────────────────────────────────────────
    def _check_sqli(self, log: LogEvent) -> Optional[dict]:
        combined = f"{log.path or ''} {log.payload or ''}"
        for pat in SQLI_PATTERNS:
            if pat.search(combined):
                return self._make_alert(
                    log,
                    threat_type="SQL Injection",
                    severity="High",
                    confidence=0.91,
                    description=f"SQL injection pattern detected in request to {log.path}",
                    mitre_tactic="TA0009",
                    mitre_technique="T1190",
                    detection_method="rule",
                )
        return None

    # ──────────────────────────────────────────────────────
    # RULE 2: Cross-Site Scripting (XSS)
    # ──────────────────────────────────────────────────────
    def _check_xss(self, log: LogEvent) -> Optional[dict]:
        combined = f"{log.path or ''} {log.payload or ''}"
        for pat in XSS_PATTERNS:
            if pat.search(combined):
                return self._make_alert(
                    log,
                    threat_type="XSS Attack",
                    severity="Medium",
                    confidence=0.85,
                    description=f"Cross-site scripting attempt detected",
                    mitre_tactic="TA0009",
                    mitre_technique="T1059.007",
                    detection_method="rule",
                )
        return None

    # ──────────────────────────────────────────────────────
    # RULE 3: Suspicious User Agent
    # ──────────────────────────────────────────────────────
    def _check_suspicious_ua(self, log: LogEvent) -> Optional[dict]:
        ua = log.user_agent or ""
        for pat in SUSPICIOUS_UA_PATTERNS:
            if pat.search(ua):
                tool = pat.pattern.replace("\\", "").replace("r", "")
                return self._make_alert(
                    log,
                    threat_type="Suspicious User Agent",
                    severity="Medium",
                    confidence=0.87,
                    description=f"Known attack tool detected in User-Agent: {ua[:100]}",
                    mitre_tactic="TA0043",
                    mitre_technique="T1595",
                    detection_method="rule",
                )
        return None

    # ──────────────────────────────────────────────────────
    # RULE 4: Brute Force (sliding window ≥5 login_fail in 60s)
    # ──────────────────────────────────────────────────────
    def _check_brute_force(self, log: LogEvent) -> Optional[dict]:
        if not (log.message and "failed login" in log.message.lower()):
            return None

        ip = log.source_ip or "unknown"
        tracker = _login_fail_tracker[ip]
        now = _now_ts()
        tracker.append(now)

        recent = [t for t in tracker if now - t < 60]
        count = len(recent)

        if count >= 5:
            severity = "Critical" if count >= 15 else "High" if count >= 8 else "Medium"
            confidence = min(0.60 + (count - 5) * 0.03, 0.99)
            return self._make_alert(
                log,
                threat_type="Brute Force",
                severity=severity,
                confidence=confidence,
                description=f"Brute force attack: {count} failed logins in last 60s from {ip}",
                mitre_tactic="TA0006",
                mitre_technique="T1110",
                detection_method="rule",
            )
        return None

    # ──────────────────────────────────────────────────────
    # RULE 5: DDoS (≥30 HTTP requests in 10s)
    # ──────────────────────────────────────────────────────
    def _check_ddos(self, log: LogEvent) -> Optional[dict]:
        if log.method not in ("GET", "POST", "PUT", "DELETE"):
            return None

        ip = log.source_ip or "unknown"
        tracker = _http_req_tracker[ip]
        now = _now_ts()
        tracker.append(now)

        recent = [t for t in tracker if now - t < 10]
        count = len(recent)

        if count >= 30:
            return self._make_alert(
                log,
                threat_type="DDoS",
                severity="Critical",
                confidence=0.88,
                description=f"DDoS detected: {count} HTTP requests in 10s from {ip}",
                mitre_tactic="TA0040",
                mitre_technique="T1498",
                detection_method="rule",
            )
        return None

    # ──────────────────────────────────────────────────────
    # RULE 6: API Abuse (≥20 API requests in 60s)
    # ──────────────────────────────────────────────────────
    def _check_api_abuse(self, log: LogEvent) -> Optional[dict]:
        if not (log.path and "/api/" in log.path):
            return None

        ip = log.source_ip or "unknown"
        tracker = _api_req_tracker[ip]
        now = _now_ts()
        tracker.append(now)

        recent = [t for t in tracker if now - t < 60]
        count = len(recent)

        if count >= 20:
            return self._make_alert(
                log,
                threat_type="API Abuse",
                severity="Medium",
                confidence=0.80,
                description=f"API rate limit exceeded: {count} requests in 60s from {ip}",
                mitre_tactic="TA0040",
                mitre_technique="T1499",
                detection_method="rule",
            )
        return None

    # ──────────────────────────────────────────────────────
    # RULE 7: Port Scan (≥5 unique ports in 30s)
    # ──────────────────────────────────────────────────────
    def _check_port_scan(self, log: LogEvent) -> Optional[dict]:
        if not (log.message and "port scan" in log.message.lower()):
            return None

        ip = log.source_ip or "unknown"
        tracker = _port_scan_tracker[ip]
        now = _now_ts()
        port = log.status_code or 0
        tracker.append((now, port))

        recent_ports = {p for t, p in tracker if now - t < 30}
        count = len(recent_ports)

        if count >= 5:
            confidence = min(0.70 + count * 0.02, 0.98)
            return self._make_alert(
                log,
                threat_type="Port Scan",
                severity="Medium",
                confidence=confidence,
                description=f"Port scan detected: {count} unique ports in 30s from {ip}",
                mitre_tactic="TA0043",
                mitre_technique="T1046",
                detection_method="rule",
            )
        return None

    # ──────────────────────────────────────────────────────
    # RULE 8: Generic Failed Login (single event marker)
    # ──────────────────────────────────────────────────────
    def _check_failed_login(self, log: LogEvent) -> Optional[dict]:
        msg = (log.message or "").lower()
        if "failed login" in msg or "authentication failure" in msg:
            return self._make_alert(
                log,
                threat_type="Failed Login",
                severity="Low",
                confidence=0.80,
                description=f"Failed authentication attempt from {log.source_ip}",
                mitre_tactic="TA0006",
                mitre_technique="T1110",
                detection_method="rule",
            )
        return None

    # ──────────────────────────────────────────────────────
    # HELPER
    # ──────────────────────────────────────────────────────
    @staticmethod
    def _make_alert(
        log: LogEvent,
        threat_type: str,
        severity: str,
        confidence: float,
        description: str,
        mitre_tactic: Optional[str] = None,
        mitre_technique: Optional[str] = None,
        detection_method: str = "rule",
    ) -> dict:
        return {
            "threat_type": threat_type,
            "severity": severity,
            "source_ip": log.source_ip or "Unknown",
            "dest_ip": log.destination_ip,
            "tenant_id": getattr(log, "tenant_id", "default") or "default",
            "confidence": confidence,
            "description": description,
            "detection_method": detection_method,
            "mitre_tactic": mitre_tactic,
            "mitre_technique": mitre_technique,
            "log_id": log.id,
            "is_correlated": False,
        }
