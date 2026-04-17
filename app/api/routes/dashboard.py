"""
Enhanced Dashboard API — comprehensive stats for the SOC overview page.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.log import LogEvent
from app.models.response_action import ResponseAction
from app.models.blocked_ip import BlockedIP

router = APIRouter()


@router.get("/")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Full dashboard overview:
    - Total counts
    - Severity breakdown
    - Threat type breakdown
    - Incident status breakdown
    - Recent alerts (last 5)
    - Recent incidents (last 5)
    - Alerts over time (last 24h, hourly)
    - Top source IPs
    """
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    # ── Totals ──────────────────────────────────────────────
    total_logs      = (await db.execute(select(func.count(LogEvent.id)))).scalar() or 0
    total_alerts    = (await db.execute(select(func.count(Alert.id)))).scalar() or 0
    total_incidents = (await db.execute(select(func.count(Incident.id)))).scalar() or 0
    total_responses = (await db.execute(select(func.count(ResponseAction.id)))).scalar() or 0
    total_blocked   = (await db.execute(select(func.count(BlockedIP.id)))).scalar() or 0

    # ── Severity breakdown ──────────────────────────────────
    sev_rows = (await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )).all()
    severity_breakdown = {row[0]: row[1] for row in sev_rows}

    # ── Threat type breakdown ───────────────────────────────
    threat_rows = (await db.execute(
        select(Alert.threat_type, func.count(Alert.id))
        .group_by(Alert.threat_type)
        .order_by(desc(func.count(Alert.id)))
        .limit(10)
    )).all()
    threat_breakdown = {row[0]: row[1] for row in threat_rows}

    # ── Incident status breakdown ───────────────────────────
    inc_status_rows = (await db.execute(
        select(Incident.status, func.count(Incident.id)).group_by(Incident.status)
    )).all()
    incident_status = {row[0]: row[1] for row in inc_status_rows}

    # ── Incident severity breakdown ─────────────────────────
    inc_sev_rows = (await db.execute(
        select(Incident.severity, func.count(Incident.id)).group_by(Incident.severity)
    )).all()
    incident_severity = {row[0]: row[1] for row in inc_sev_rows}

    # ── Top source IPs ──────────────────────────────────────
    top_ip_rows = (await db.execute(
        select(Alert.source_ip, func.count(Alert.id).label("count"))
        .group_by(Alert.source_ip)
        .order_by(desc(func.count(Alert.id)))
        .limit(10)
    )).all()
    top_ips = [{"ip": row[0], "count": row[1]} for row in top_ip_rows]

    # ── Recent alerts ───────────────────────────────────────
    recent_alert_rows = (await db.execute(
        select(Alert).order_by(Alert.timestamp.desc()).limit(10)
    )).scalars().all()
    recent_alerts = [
        {
            "id": a.id,
            "threat_type": a.threat_type,
            "severity": a.severity,
            "source_ip": a.source_ip,
            "confidence": a.confidence,
            "detection_method": a.detection_method,
            "mitre_tactic": a.mitre_tactic,
            "mitre_technique": a.mitre_technique,
            "timestamp": a.timestamp,
        }
        for a in recent_alert_rows
    ]

    # ── Recent incidents ────────────────────────────────────
    recent_inc_rows = (await db.execute(
        select(Incident).order_by(Incident.timestamp.desc()).limit(10)
    )).scalars().all()
    recent_incidents = [
        {
            "id": i.id,
            "title": i.title,
            "incident_type": i.incident_type,
            "severity": i.severity,
            "risk_score": i.risk_score,
            "risk_level": i.risk_level,
            "status": i.status,
            "source_ips": i.source_ips,
            "requires_immediate_action": i.requires_immediate_action,
            "timestamp": i.timestamp,
        }
        for i in recent_inc_rows
    ]

    # ── Detection method breakdown ──────────────────────────
    method_rows = (await db.execute(
        select(Alert.detection_method, func.count(Alert.id)).group_by(Alert.detection_method)
    )).all()
    detection_methods = {row[0]: row[1] for row in method_rows}

    return {
        "summary": {
            "total_logs": total_logs,
            "total_alerts": total_alerts,
            "total_incidents": total_incidents,
            "total_responses": total_responses,
            "total_blocked_ips": total_blocked,
        },
        "alert_severity_breakdown": severity_breakdown,
        "threat_type_breakdown": threat_breakdown,
        "incident_status_breakdown": incident_status,
        "incident_severity_breakdown": incident_severity,
        "detection_method_breakdown": detection_methods,
        "top_source_ips": top_ips,
        "recent_alerts": recent_alerts,
        "recent_incidents": recent_incidents,
    }
