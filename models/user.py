from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # 'admin' | 'agent'
    phone = Column(String(20), nullable=True)
    fcm_token = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    assigned_customers = relationship("Customer", back_populates="agent", foreign_keys="Customer.assigned_agent_id")
    collections = relationship("Collection", back_populates="agent", foreign_keys="Collection.agent_id")
    va_requests = relationship("VaRequest", back_populates="agent", foreign_keys="VaRequest.agent_id")
    activity_logs = relationship("ActivityLog", back_populates="user")
