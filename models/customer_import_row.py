from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from core.database import Base


class CustomerImportRow(Base):
    __tablename__ = "customer_import_rows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    upload_batch = Column(String(100), nullable=False, index=True)
    source_partner_name = Column(String(100), nullable=True, index=True)
    source_partner_code = Column(String(100), nullable=True, index=True)
    source_file_name = Column(String(255), nullable=True, index=True)
    source_sheet_name = Column(String(100), nullable=True)
    source_row_number = Column(Integer, nullable=True, index=True)
    mapping_profile_name = Column(String(100), nullable=True)
    import_version = Column(String(50), nullable=True)
    import_status = Column(String(30), nullable=False, default="imported", index=True)
    import_error_flag = Column(Integer, default=0, index=True)
    import_error_message = Column(Text, nullable=True)
    imported_at = Column(DateTime, default=func.now())
    raw_customer_name = Column(String(255), nullable=True)
    raw_nik = Column(String(100), nullable=True)
    raw_phone = Column(String(50), nullable=True)
    raw_phone_2 = Column(String(50), nullable=True)
    raw_address = Column(Text, nullable=True)
    raw_city = Column(String(100), nullable=True)
    raw_due_date = Column(String(100), nullable=True)
    raw_disbursement_date = Column(String(100), nullable=True)
    raw_loan_amount = Column(String(100), nullable=True)
    raw_installment_amount = Column(String(100), nullable=True)
    raw_outstanding_amount = Column(String(100), nullable=True)
    raw_overdue_days = Column(String(100), nullable=True)
    raw_lat = Column(String(100), nullable=True)
    raw_lng = Column(String(100), nullable=True)
    raw_lat_lng = Column(String(255), nullable=True)
    raw_platform_name = Column(String(100), nullable=True)
    raw_status = Column(String(100), nullable=True)
    raw_payload = Column(Text, nullable=True)

    customer = relationship("Customer", back_populates="import_rows")
