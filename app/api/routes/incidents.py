"""
Enhanced Incidents API
Full CRUD + status changes + reporting
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.db.session import get_db
from app.schemas.incident import Incident, IncidentCreate
from app.models.incident import Incident as IncidentModel

router = APIRouter()


@router.get("/", response_model=List[Incident])
async def get_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all incidents with optional filters."""
    query = select(IncidentModel).options(
        selectinload(IncidentModel.alerts),
        selectinload(IncidentModel.responses),
    ).order_by(IncidentModel.timestamp.desc())

    if status:
        query = query.where(IncidentModel.status == status)
    if severity:
        query = query.where(IncidentModel.severity == severity)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific incident by ID."""
    query = select(IncidentModel).options(
        selectinload(IncidentModel.alerts),
        selectinload(IncidentModel.responses),
    ).where(IncidentModel.id == incident_id)

    result = await db.execute(query)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}/status")
async def update_incident_status(
    incident_id: int,
    status: str = Query(..., description="New status: Open | Investigating | Resolved | Closed"),
    db: AsyncSession = Depends(get_db),
):
    """Change the status of an incident (Open → Investigating → Resolved)."""
    valid = {"Open", "Investigating", "Resolved", "Closed"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid}")

    query = select(IncidentModel).where(IncidentModel.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = status
    await db.commit()
    await db.refresh(incident)
    return {"id": incident.id, "status": incident.status}


@router.get("/{incident_id}/report")
async def generate_incident_report(incident_id: int, db: AsyncSession = Depends(get_db)):
    """Incident Report Generator — timeline, root cause, recommendations."""
    query = select(IncidentModel).options(
        selectinload(IncidentModel.alerts),
        selectinload(IncidentModel.responses),
    ).where(IncidentModel.id == incident_id)

    result = await db.execute(query)
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    timeline = sorted(
        [{"type": "alert", "timestamp": str(a.timestamp), "detail": a.threat_type, "severity": a.severity, "source_ip": a.source_ip} for a in incident.alerts] +
        [{"type": "response", "timestamp": str(r.timestamp), "detail": r.action_type, "status": r.status} for r in incident.responses],
        key=lambda x: x["timestamp"],
    )

    return {
        "incident_id": incident.id,
        "title": incident.title,
        "incident_type": incident.incident_type,
        "status": incident.status,
        "severity": incident.severity,
        "risk_score": incident.risk_score,
        "risk_level": incident.risk_level,
        "requires_immediate_action": incident.requires_immediate_action,
        "source_ips": incident.source_ips or [],
        "affected_systems": list(set([a.source_ip for a in incident.alerts])),
        "root_cause": incident.root_cause,
        "recommendations": incident.recommendations,
        "mitre_tactics": list({a.mitre_tactic for a in incident.alerts if a.mitre_tactic}),
        "mitre_techniques": list({a.mitre_technique for a in incident.alerts if a.mitre_technique}),
        "timeline": timeline,
        "alert_count": len(incident.alerts),
        "response_count": len(incident.responses),
    }
