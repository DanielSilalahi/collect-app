from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False, index=True)
    nick_name = Column(String(255), nullable=True)
    customer_code = Column(String(100), nullable=True, index=True)
    external_customer_id = Column(String(100), nullable=True, index=True)
    platform_name = Column(String(100), nullable=True, index=True)
    partner_name = Column(String(100), nullable=True, index=True)
    nik = Column(String(100), nullable=True, index=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    primary_phone = Column(String(50), nullable=True, index=True)
    primary_city = Column(String(100), nullable=True, index=True)
    primary_address_summary = Column(Text, nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="new", index=True)
    sub_status = Column(String(50), nullable=True, index=True)
    current_loan_id = Column(Integer, ForeignKey("customer_loans.id"), nullable=True, index=True)
    current_dpd = Column(Integer, nullable=True, index=True)
    current_total_outstanding = Column(Numeric(18, 2), nullable=True)
    last_payment_date = Column(Date, nullable=True)
    last_payment_amount = Column(Numeric(18, 2), nullable=True)
    last_contacted_at = Column(DateTime, nullable=True)
    upload_batch = Column(String(100), nullable=True, index=True)
    search_name = Column(String(255), nullable=True, index=True)
    search_nik = Column(String(255), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted = Column(Integer, default=0, index=True)

    agent = relationship("User", back_populates="assigned_customers", foreign_keys=[assigned_agent_id])
    current_loan = relationship("CustomerLoan", foreign_keys=[current_loan_id], post_update=True)
    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan")
    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    loans = relationship(
        "CustomerLoan",
        back_populates="customer",
        foreign_keys="CustomerLoan.customer_id",
        cascade="all, delete-orphan",
    )
    import_rows = relationship("CustomerImportRow", back_populates="customer", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="customer", cascade="all, delete-orphan")
    va_requests = relationship("VaRequest", back_populates="customer")
