from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class CustomerResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: str
    notes: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomerDetailResponse(CustomerResponse):
    agent_name: Optional[str] = None
    va_number: Optional[str] = None
    va_bank: Optional[str] = None
    va_amount: Optional[int] = None
    va_request_status: Optional[str] = None
    collections: List["CollectionBriefResponse"] = []


class CollectionBriefResponse(BaseModel):
    id: int
    status: str
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class CustomerStats(BaseModel):
    total: int
    bayar: int
    janji_bayar: int
    belum: int
    tidak_ketemu: int


class PaginatedCustomerResponse(BaseModel):
    customers: List[CustomerResponse]
    stats: CustomerStats
    total_count: int


CustomerDetailResponse.model_rebuild()
