from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.visit_status import VisitStatus
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/collections", tags=["Collection API"])

class VisitStatusResponse(BaseModel):
    id: int
    key: str
    label: str
    color_code: str
    icon: str
    is_ptp: bool
    is_active: bool
    display_order: int

    class Config:
        from_attributes = True

@router.get("/statuses", response_model=List[VisitStatusResponse])
def get_visit_statuses(db: Session = Depends(get_db)):
    """Fetch active visit statuses for the mobile app."""
    return db.query(VisitStatus).filter(VisitStatus.is_active == True).order_by(VisitStatus.display_order).all()
