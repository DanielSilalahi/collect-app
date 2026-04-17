from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from datetime import datetime
from core.database import Base
from sqlalchemy.orm import relationship

class FieldSetting(Base):
    __tablename__ = "field_settings"

    field_key = Column(String(100), primary_key=True)
    is_priority = Column(Boolean, default=False)
    display_order = Column(Integer, default=100)
    category_id = Column(Integer, ForeignKey("field_categories.id"), nullable=True)
    category_override = Column(String(50), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship to category
    category = relationship("FieldCategory", back_populates="settings")

    def __repr__(self):
        return f"<FieldSetting(key={self.field_key}, priority={self.is_priority})>"
