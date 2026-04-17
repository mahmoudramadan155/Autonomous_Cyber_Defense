from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship

class LogEvent(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), index=True) # e.g. Linux, Nginx, FortiGate, API
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Normalized fields
    source_ip = Column(String(50), index=True, nullable=True)
    destination_ip = Column(String(50), nullable=True)
    tenant_id = Column(String(50), default="default", index=True)
    user_agent = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    path = Column(String(255), nullable=True)
    status_code = Column(Integer, nullable=True)
    payload = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    
    # Optional relation to alert
    alerts = relationship("Alert", back_populates="log")
