from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Numeric, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base


class CustomerArchive(Base):
    __tablename__ = "customer_archives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_customer_id = Column(Integer, nullable=False, index=True)
    full_name = Column(String(255), nullable=True, index=True)
    nik = Column(String(100), nullable=True, index=True)
    primary_phone = Column(String(50), nullable=True, index=True)
    upload_batch = Column(String(100), nullable=True, index=True)
    loan_number = Column(String(100), nullable=True, index=True)
    total_outstanding = Column(Numeric(18, 2), nullable=True)
    overdue_days = Column(Integer, nullable=True)
    status = Column(String(30), nullable=True, index=True)
    
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column(DateTime, default=func.now())
    
    # Store everything related to the customer in a giant JSON blob
    # Includes: Customer profile, Current Loan, Addresses, Contacts
    full_data_json = Column(JSON, nullable=False)

    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
