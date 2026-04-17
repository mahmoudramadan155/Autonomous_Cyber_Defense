from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.db.session import get_db
from app.schemas.alert import Alert
from app.models.alert import Alert as AlertModel

router = APIRouter()


@router.get("/", response_model=List[Alert])
async def get_alerts(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    threat_type: Optional[str] = None,
    source_ip: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve alerts with optional filters."""
    query = select(AlertModel).order_by(AlertModel.timestamp.desc())

    if severity:
        query = query.where(AlertModel.severity == severity)
    if threat_type:
        query = query.where(AlertModel.threat_type == threat_type)
    if source_ip:
        query = query.where(AlertModel.source_ip == source_ip)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific alert by ID."""
    query = select(AlertModel).where(AlertModel.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
