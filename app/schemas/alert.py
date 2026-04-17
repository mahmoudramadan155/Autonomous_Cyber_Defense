from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AlertBase(BaseModel):
    threat_type: str
    tenant_id: str = "default"
    severity: str
    source_ip: str
    dest_ip: Optional[str] = None
    confidence: float
    description: Optional[str] = None
    detection_method: str = "rule"
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    log_id: Optional[int] = None
    is_correlated: bool = False
    incident_id: Optional[int] = None


class AlertCreate(AlertBase):
    pass


class Alert(AlertBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
