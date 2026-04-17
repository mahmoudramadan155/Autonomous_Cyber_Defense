"""
Blocked IPs Management API
Endpoints: block_ip, unblock_ip, list blocked IPs
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.blocked_ip import BlockedIP as BlockedIPModel
from app.schemas.blocked_ip import BlockedIP, BlockedIPCreate

router = APIRouter()


@router.get("/", response_model=List[BlockedIP])
async def list_blocked_ips(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all currently blocked IPs."""
    query = select(BlockedIPModel).order_by(BlockedIPModel.blocked_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=BlockedIP, status_code=201)
async def block_ip(
    body: BlockedIPCreate,
    db: AsyncSession = Depends(get_db),
):
    """Block an IP address."""
    # Check if already blocked
    existing = await db.execute(
        select(BlockedIPModel).where(BlockedIPModel.ip_address == body.ip_address)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"IP {body.ip_address} is already blocked")

    record = BlockedIPModel(**body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{ip}", status_code=204)
async def unblock_ip(ip: str, db: AsyncSession = Depends(get_db)):
    """Unblock an IP address."""
    query = select(BlockedIPModel).where(BlockedIPModel.ip_address == ip)
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail=f"IP {ip} is not in the blocklist")

    await db.delete(record)
    await db.commit()
