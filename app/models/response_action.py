from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship

class ResponseAction(Base):
    __tablename__ = "response_actions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    action_type = Column(String(100)) # e.g., Block IP, Disable User, Rate Limit Endpoint, Send Alert
    target = Column(String(255)) # IP address, username, endpoint
    status = Column(String(50), default="Pending") # Pending, Success, Failed, Manual Approval Required
    executed_by = Column(String(50), default="Auto") # Auto, User
    details = Column(Text, nullable=True)
    
    incident = relationship("Incident", back_populates="responses")
