from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class BlockedIPBase(BaseModel):
    ip_address: str
    reason: str
    blocked_by: str = "system"
    tenant_id: str = "default"
    details: Optional[str] = None
    expires_at: Optional[datetime] = None


class BlockedIPCreate(BlockedIPBase):
    pass


class BlockedIP(BlockedIPBase):
    id: int
    blocked_at: datetime

    model_config = ConfigDict(from_attributes=True)
