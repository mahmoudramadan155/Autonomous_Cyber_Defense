from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.session import Base


class BlockedIP(Base):
    __tablename__ = "blocked_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), unique=True, index=True)
    reason = Column(String(200))
    blocked_by = Column(String(100), default="system")  # system | manual
    tenant_id = Column(String(50), default="default", index=True)
    details = Column(Text, nullable=True)
    blocked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
