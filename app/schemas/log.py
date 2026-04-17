from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

class LogEventBase(BaseModel):
    source: str
    tenant_id: str = "default"
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    user_agent: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    payload: Optional[str] = None
    message: Optional[str] = None

class LogEventCreate(LogEventBase):
    pass

class LogEvent(LogEventBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
