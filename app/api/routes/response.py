from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import get_db
from app.schemas.response_action import ResponseAction, ResponseActionCreate
from app.models.response_action import ResponseAction as ResponseActionModel
from app.services.response_engine import ResponseEngine
import logging

router = APIRouter()

@router.get("/", response_model=List[ResponseAction])
async def get_responses(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all response actions."""
    query = select(ResponseActionModel).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/execute", response_model=ResponseAction)
async def execute_response(body: ResponseActionCreate, db: AsyncSession = Depends(get_db)):
    """
    Execute a SOAR-lite response action.
    Set executed_by = 'Auto' for auto-mode or anything else for manual approval.
    """
    engine = ResponseEngine(db)
    mode = "auto" if body.executed_by == "Auto" else "manual"
    action = await engine.execute_action(
        incident_id=body.incident_id,
        action_type=body.action_type,
        target=body.target,
        mode=mode
    )
    return action

@router.post("/{action_id}/approve", response_model=ResponseAction)
async def approve_manual_action(action_id: int, db: AsyncSession = Depends(get_db)):
    """Approve a pending manual response action."""
    query = select(ResponseActionModel).where(ResponseActionModel.id == action_id)
    result = await db.execute(query)
    action = result.scalar_one_or_none()

    if not action:
        logging.error(f"Failed manual approval: Action {action_id} not found.")
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status != "Manual Approval Required":
        logging.warning(f"Failed manual approval: Action {action_id} not pending approval (Status: {action.status})")
        raise HTTPException(status_code=400, detail="Action is not pending manual approval")

    action.status = "Success"
    action.executed_by = "Human Approved"
    await db.commit()
    await db.refresh(action)
    
    logging.info(f"Manual action {action_id} officially APPROVED by human operator. Action executed.")
    return action
