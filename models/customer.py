from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    upload_batch = Column(String(100), nullable=True, index=True)
    status = Column(String(20), default="belum", index=True)  # belum | janji_bayar | bayar
    notes = Column(Text, nullable=True)
    
    # P2P Specific Fields
    loan_number = Column(String(100), nullable=True, index=True)
    platform_name = Column(String(100), nullable=True)
    outstanding_amount = Column(Float, nullable=True)
    due_date = Column(DateTime, nullable=True)
    overdue_days = Column(Integer, nullable=True)
    emergency_contact_1_name = Column(String(255), nullable=True)
    emergency_contact_1_phone = Column(String(50), nullable=True)
    emergency_contact_2_name = Column(String(255), nullable=True)
    emergency_contact_2_phone = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    is_deleted = Column(Integer, default=0, index=True) # Using Integer (0/1) for better cross-DB compatibility, mapped to boolean logic


    # Relationships
    agent = relationship("User", back_populates="assigned_customers", foreign_keys=[assigned_agent_id])
    collections = relationship("Collection", back_populates="customer", cascade="all, delete-orphan")
    va_requests = relationship("VaRequest", back_populates="customer", cascade="all, delete-orphan")
