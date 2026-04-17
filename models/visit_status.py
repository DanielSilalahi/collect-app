from sqlalchemy import Column, String, Boolean, Integer
from core.database import Base

class VisitStatus(Base):
    __tablename__ = "visit_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False) # e.g. "bayar"
    label = Column(String(100), nullable=False)          # e.g. "Bayar"
    color_code = Column(String(20), default="#10B981")   # Hex color
    icon = Column(String(50), default="bi-check-circle") # Bootstrap icon class
    is_ptp = Column(Boolean, default=False)              # If true, maybe trigger PTP logic
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    def __repr__(self):
        return f"<VisitStatus(label={self.label}, key={self.key})>"
