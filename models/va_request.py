from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base


class VaRequest(Base):
    __tablename__ = "va_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="pending", index=True)  # pending | completed
    is_notified_to_agent = Column(Integer, default=0) # using integer 0/1 for sqlite boolean compat
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="va_requests")
    agent = relationship("User", back_populates="va_requests", foreign_keys=[agent_id])
    va_data = relationship("VaData", back_populates="va_request", uselist=False, cascade="all, delete-orphan")
