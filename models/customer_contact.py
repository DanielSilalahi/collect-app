from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from core.database import Base


class CustomerContact(Base):
    __tablename__ = "customer_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    contact_type = Column(String(30), nullable=False, index=True)
    contact_role = Column(String(30), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    relationship_label = Column("relationship", String(100), nullable=True)
    phone_number = Column(String(50), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    is_primary = Column(Integer, default=0, index=True)
    priority_order = Column(Integer, nullable=True, index=True)
    is_whatsapp = Column(Integer, default=0, index=True)
    is_active = Column(Integer, default=1, index=True)
    is_verified = Column(Integer, default=0, index=True)
    is_valid = Column(Integer, default=1, index=True)
    verification_source = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="contacts")
