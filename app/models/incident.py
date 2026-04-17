from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    title = Column(String(200))
    incident_type = Column(String(100), default="unknown")  # account_compromise, web_attack, ddos, etc.
    status = Column(String(50), default="Open")             # Open, Investigating, Resolved, Closed
    severity = Column(String(20), index=True)
    tenant_id = Column(String(50), default="default", index=True)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="Low")
    source_ips = Column(JSON, default=list)                 # List of source IPs
    description = Column(Text)
    root_cause = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    requires_immediate_action = Column(Boolean, default=False)

    alerts = relationship("Alert", back_populates="incident")
    responses = relationship("ResponseAction", back_populates="incident")
