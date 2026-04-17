from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Open")  # Open, In Progress, Closed
    priority = Column(String(20), default="Medium")  # Low, Medium, High, Critical
    assigned_to = Column(String(100), nullable=True)
    tenant_id = Column(String(50), default="default", index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    incident = relationship("Incident", backref="cases")
