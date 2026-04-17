from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "Open"
    priority: str = "Medium"
    assigned_to: Optional[str] = None
    tenant_id: str = "default"
    incident_id: Optional[int] = None
    notes: Optional[str] = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class Case(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
