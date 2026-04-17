from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    log_id = Column(Integer, ForeignKey("logs.id"), nullable=True)
    threat_type = Column(String(100), index=True)  # e.g. SQL Injection, Brute Force
    severity = Column(String(20), index=True)       # Low, Medium, High, Critical
    source_ip = Column(String(50), index=True)
    dest_ip = Column(String(50), nullable=True)
    tenant_id = Column(String(50), default="default", index=True)
    confidence = Column(Float)
    description = Column(Text, nullable=True)
    detection_method = Column(String(50), default="rule")  # rule, ml, anomaly
    mitre_tactic = Column(String(50), nullable=True)
    mitre_technique = Column(String(50), nullable=True)
    is_correlated = Column(Boolean, default=False)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)

    log = relationship("LogEvent", back_populates="alerts")
    incident = relationship("Incident", back_populates="alerts")
