"""
Enhanced Risk Scoring Engine
Formula: score = (severity_base × asset_value × incident_type_mult × time_of_day_mult) + frequency_bonus
"""
from datetime import datetime, timezone


class RiskScoringEngine:

    SEVERITY_BASE = {
        "Low": 20,
        "Medium": 50,
        "High": 70,
        "Critical": 90,
    }

    INCIDENT_TYPE_MULT = {
        "account_compromise": 1.5,
        "api_injection": 1.5,
        "ddos": 1.4,
        "web_attack": 1.3,
        "recon_attack": 1.2,
        "automated_attack": 1.1,
        "brute_force": 1.2,
        "coordinated_attack": 1.3,
        "unknown": 1.0,
    }

    # High-value target IPs (in a real deployment, loaded from config)
    CRITICAL_ASSETS: dict[str, float] = {
        "10.0.0.10": 2.0,   # DB server
        "10.0.0.11": 2.0,   # Auth server
        "10.0.0.12": 1.6,   # API Gateway
        "10.0.0.1":  1.4,   # Core router
    }

    def calculate_risk_score(
        self,
        incident_type: str = "unknown",
        severity: str = "Medium",
        alert_count: int = 1,
        source_ips: list[str] | None = None,
    ) -> float:
        """
        Returns a risk score 0-100.
        """
        base = self.SEVERITY_BASE.get(severity, 5)

        # Asset value multiplier
        asset_mult = 1.0
        for ip in (source_ips or []):
            asset_mult = max(asset_mult, self.CRITICAL_ASSETS.get(ip, 1.0))

        # Incident type multiplier
        type_mult = self.INCIDENT_TYPE_MULT.get(incident_type, 1.0)

        # Time-of-day multiplier (00:00–06:00 UTC is riskier)
        hour = datetime.now(timezone.utc).hour
        time_mult = 1.2 if 0 <= hour < 6 else 1.0

        # Frequency bonus (+2 per alert, max +20)
        freq_bonus = min(alert_count * 2, 20)

        score = (base * asset_mult * type_mult * time_mult) + freq_bonus
        return round(min(score, 100.0), 2)

    @staticmethod
    def risk_level(score: float) -> str:
        if score >= 80:
            return "Critical"
        if score >= 60:
            return "High"
        if score >= 40:
            return "Medium"
        return "Low"

    def enrich_incident(self, incident: dict) -> dict:
        """Adds risk_score and risk_level to an incident dict."""
        score = self.calculate_risk_score(
            incident_type=incident.get("incident_type", "unknown"),
            severity=incident.get("severity", "Medium"),
            alert_count=len(incident.get("alert_ids", [])),
            source_ips=incident.get("source_ips", []),
        )
        incident["risk_score"] = score
        incident["risk_level"] = self.risk_level(score)
        incident["requires_immediate_action"] = score >= 75
        return incident
