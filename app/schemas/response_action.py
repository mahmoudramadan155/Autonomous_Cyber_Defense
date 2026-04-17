from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ResponseActionBase(BaseModel):
    incident_id: Optional[int] = None
    action_type: str
    target: str
    status: str = "Pending"
    executed_by: str = "Auto"
    details: Optional[str] = None

class ResponseActionCreate(ResponseActionBase):
    pass

class ResponseAction(ResponseActionBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
