from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class VaRequestCreate(BaseModel):
    customer_id: int
    notes: Optional[str] = None


class VaRequestResponse(BaseModel):
    id: int
    customer_id: int
    agent_id: int
    notes: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    va_number: Optional[str] = None
    va_bank: Optional[str] = None
    va_amount: Optional[int] = None

    class Config:
        from_attributes = True


class VaDataCreate(BaseModel):
    va_number: str
    bank_name: str
    amount: Optional[int] = None
