from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from core.database import Base


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    address_type = Column(String(30), nullable=False, index=True)
    label = Column(String(100), nullable=True)
    recipient_name = Column(String(255), nullable=True)
    full_address = Column(Text, nullable=False)
    street = Column(String(255), nullable=True)
    block = Column(String(100), nullable=True)
    house_number = Column(String(100), nullable=True)
    rt = Column(String(20), nullable=True)
    rw = Column(String(20), nullable=True)
    kelurahan = Column(String(100), nullable=True)
    kecamatan = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    province = Column(String(100), nullable=True, index=True)
    postal_code = Column(String(20), nullable=True, index=True)
    country = Column(String(100), nullable=True)
    landmark = Column(String(255), nullable=True)
    address_note = Column(Text, nullable=True)
    residence_status = Column(String(100), nullable=True)
    is_primary = Column(Integer, default=0, index=True)
    is_active = Column(Integer, default=1, index=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    map_url = Column(String(500), nullable=True)
    coordinate_source = Column(String(100), nullable=True)
    coordinate_accuracy_meters = Column(Float, nullable=True)
    is_location_verified = Column(Integer, default=0, index=True)
    raw_lat = Column(String(100), nullable=True)
    raw_lng = Column(String(100), nullable=True)
    raw_lat_lng = Column(String(255), nullable=True)
    raw_map_link = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="addresses")
