from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class CollectionCreateRequest(BaseModel):
    customer_id: int
    status: str  # bayar | janji_bayar | tidak_ketemu
    notes: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    timestamp: datetime


class CollectionSyncRequest(BaseModel):
    """Batch sync from offline queue."""
    items: List[CollectionCreateRequest]


class CollectionResponse(BaseModel):
    id: int
    customer_id: int
    agent_id: int
    status: str
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    timestamp: datetime
    synced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
