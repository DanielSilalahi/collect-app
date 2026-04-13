from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # bayar | janji_bayar | tidak_ketemu
    notes = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="collections")
    agent = relationship("User", back_populates="collections", foreign_keys=[agent_id])
