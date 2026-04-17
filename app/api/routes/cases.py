"""
Case Management API
Endpoints: CRUD for analyst cases
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.case import Case as CaseModel
from app.schemas.case import Case, CaseCreate, CaseUpdate

router = APIRouter()


@router.get("/", response_model=List[Case])
async def list_cases(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all cases, optionally filtered by status."""
    query = select(CaseModel).order_by(CaseModel.created_at.desc())
    if status:
        query = query.where(CaseModel.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=Case, status_code=201)
async def create_case(body: CaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new analyst case."""
    case = CaseModel(**body.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/{case_id}", response_model=Case)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific case by ID."""
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=Case)
async def update_case(
    case_id: int,
    body: CaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a case (notes, status, assignment, etc.)."""
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(case, field, value)

    await db.commit()
    await db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a case."""
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    await db.delete(case)
    await db.commit()
