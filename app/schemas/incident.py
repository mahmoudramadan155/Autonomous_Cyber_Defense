from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from .alert import Alert
from .response_action import ResponseAction


class IncidentBase(BaseModel):
    title: str
    incident_type: str = "unknown"
    tenant_id: str = "default"
    status: str = "Open"
    severity: str
    risk_score: float = 0.0
    risk_level: str = "Low"
    source_ips: List[str] = []
    description: str
    root_cause: Optional[str] = None
    recommendations: Optional[str] = None
    requires_immediate_action: bool = False


class IncidentCreate(IncidentBase):
    pass


class Incident(IncidentBase):
    id: int
    timestamp: datetime
    alerts: List[Alert] = []
    responses: List[ResponseAction] = []

    model_config = ConfigDict(from_attributes=True)
