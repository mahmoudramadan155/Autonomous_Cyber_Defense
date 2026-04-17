"""
Search API — full-text search across alerts, incidents, and logs.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func

from app.db.session import get_db
from app.models.alert import Alert as AlertModel
from app.models.incident import Incident as IncidentModel
from app.models.log import LogEvent

router = APIRouter()


@router.get("/")
async def search(
    q: str = Query(..., description="Search query"),
    kind: Optional[str] = Query(None, description="Filter by type: alerts | incidents | logs"),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Global search across alerts, incidents, and logs.
    Supports searching by source IP, threat type, title, description.
    """
    results = {}
    q_lower = f"%{q.lower()}%"

    if kind in (None, "alerts"):
        alert_query = select(AlertModel).where(
            or_(
                func.lower(AlertModel.source_ip).like(q_lower),
                func.lower(AlertModel.threat_type).like(q_lower),
                func.lower(AlertModel.description).like(q_lower),
                func.lower(AlertModel.severity).like(q_lower),
            )
        ).order_by(AlertModel.timestamp.desc()).limit(limit)
        alert_rows = (await db.execute(alert_query)).scalars().all()
        results["alerts"] = [
            {
                "id": a.id,
                "threat_type": a.threat_type,
                "severity": a.severity,
                "source_ip": a.source_ip,
                "confidence": a.confidence,
                "timestamp": a.timestamp,
                "mitre_tactic": a.mitre_tactic,
                "mitre_technique": a.mitre_technique,
            }
            for a in alert_rows
        ]

    if kind in (None, "incidents"):
        inc_query = select(IncidentModel).where(
            or_(
                func.lower(IncidentModel.title).like(q_lower),
                func.lower(IncidentModel.description).like(q_lower),
                func.lower(IncidentModel.severity).like(q_lower),
                func.lower(IncidentModel.incident_type).like(q_lower),
            )
        ).order_by(IncidentModel.timestamp.desc()).limit(limit)
        inc_rows = (await db.execute(inc_query)).scalars().all()
        results["incidents"] = [
            {
                "id": i.id,
                "title": i.title,
                "severity": i.severity,
                "risk_score": i.risk_score,
                "risk_level": i.risk_level,
                "incident_type": i.incident_type,
                "timestamp": i.timestamp,
            }
            for i in inc_rows
        ]

    if kind in (None, "logs"):
        log_query = select(LogEvent).where(
            or_(
                func.lower(LogEvent.source_ip).like(q_lower),
                func.lower(LogEvent.path).like(q_lower),
                func.lower(LogEvent.payload).like(q_lower),
                func.lower(LogEvent.message).like(q_lower),
            )
        ).order_by(LogEvent.timestamp.desc()).limit(limit)
        log_rows = (await db.execute(log_query)).scalars().all()
        results["logs"] = [
            {
                "id": lg.id,
                "source": lg.source,
                "source_ip": lg.source_ip,
                "path": lg.path,
                "method": lg.method,
                "status_code": lg.status_code,
                "timestamp": lg.timestamp,
            }
            for lg in log_rows
        ]

    return {"query": q, "results": results}


@router.get("/by_ip/{ip}")
async def search_by_ip(ip: str, db: AsyncSession = Depends(get_db)):
    """Find all alerts and incidents involving a specific IP."""
    alerts = (await db.execute(
        select(AlertModel)
        .where(AlertModel.source_ip == ip)
        .order_by(AlertModel.timestamp.desc())
        .limit(50)
    )).scalars().all()

    incidents = (await db.execute(
        select(IncidentModel)
        .order_by(IncidentModel.timestamp.desc())
        .limit(50)
    )).scalars().all()

    # Filter incidents where source_ips JSON contains the IP
    matching_incidents = [i for i in incidents if ip in (i.source_ips or [])]

    return {
        "ip": ip,
        "alerts": [
            {"id": a.id, "threat_type": a.threat_type, "severity": a.severity, "timestamp": a.timestamp}
            for a in alerts
        ],
        "incidents": [
            {"id": i.id, "title": i.title, "severity": i.severity, "risk_score": i.risk_score, "timestamp": i.timestamp}
            for i in matching_incidents
        ],
    }
