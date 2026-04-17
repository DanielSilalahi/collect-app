from sqlalchemy import Column, String, Boolean, Integer, Text
from core.database import Base
from sqlalchemy.orm import relationship

class FieldCategory(Base):
    __tablename__ = "field_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False)
    label = Column(String(100), nullable=False)
    icon = Column(String(50), default="bi-folder")
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)  # If True, cannot be deleted

    # Relationship to settings
    settings = relationship("FieldSetting", back_populates="category")

    def __repr__(self):
        return f"<FieldCategory(label={self.label}, is_system={self.is_system})>"
