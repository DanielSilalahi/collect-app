from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    primary_phone: Optional[str] = None
    primary_city: Optional[str] = None
    primary_address_summary: Optional[str] = None
    platform_name: Optional[str] = None
    status: str
    sub_status: Optional[str] = None
    current_dpd: Optional[int] = None
    current_total_outstanding: Optional[Decimal] = None
    assigned_agent_id: Optional[int] = None
    created_at: Optional[datetime] = None


class CustomerLoanBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    loan_number: Optional[str] = None
    contract_number: Optional[str] = None
    total_outstanding: Optional[Decimal] = None
    overdue_days: Optional[int] = None


class CustomerContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact_type: str
    contact_role: Optional[str] = None
    name: Optional[str] = None
    relationship_label: Optional[str] = Field(default=None, alias="relationship")
    phone_number: Optional[str] = None
    email: Optional[str] = None
    is_primary: int = 0


class CustomerAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address_type: str
    full_address: str
    city: Optional[str] = None
    province: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    raw_lat_lng: Optional[str] = None
    is_primary: int = 0


class CollectionBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    timestamp: datetime


class CustomerDetailResponse(CustomerResponse):
    agent_name: Optional[str] = None
    current_loan: Optional[CustomerLoanBriefResponse] = None
    contacts: List[CustomerContactResponse] = Field(default_factory=list)
    addresses: List[CustomerAddressResponse] = Field(default_factory=list)
    collections: List[CollectionBriefResponse] = Field(default_factory=list)


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
