from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base


class VaData(Base):
    __tablename__ = "va_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    va_request_id = Column(Integer, ForeignKey("va_requests.id"), nullable=False, unique=True, index=True)
    va_number = Column(String(100), nullable=False)
    bank_name = Column(String(100), nullable=False)
    amount = Column(BigInteger, nullable=True)
    created_by_admin = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    va_request = relationship("VaRequest", back_populates="va_data")
    admin = relationship("User", foreign_keys=[created_by_admin])
