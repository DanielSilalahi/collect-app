from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.dependencies import get_current_user_api
from models.user import User
from models.customer import Customer
from models.collection import Collection
from models.va_request import VaRequest
from models.va_data import VaData
from schemas.customer import CustomerResponse, CustomerDetailResponse, CollectionBriefResponse
from typing import Optional

router = APIRouter(prefix="/api/customers", tags=["Customer API"])


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    status: Optional[str] = Query(None),
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """List customers assigned to current agent."""
    query = db.query(Customer).filter(Customer.assigned_agent_id == user.id)

    if status:
        query = query.filter(Customer.status == status)

    customers = query.order_by(Customer.name.asc()).all()
    return [CustomerResponse.model_validate(c) for c in customers]


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    customer_id: int,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Get customer detail with VA info and collection history."""
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.assigned_agent_id == user.id)
        .first()
    )
    if not customer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")

    # Get latest VA request
    va_req = (
        db.query(VaRequest)
        .filter(VaRequest.customer_id == customer_id)
        .order_by(VaRequest.created_at.desc())
        .first()
    )

    va_number = None
    va_bank = None
    va_amount = None
    va_request_status = None

    if va_req:
        va_request_status = va_req.status
        if va_req.va_data:
            va_number = va_req.va_data.va_number
            va_bank = va_req.va_data.bank_name
            va_amount = va_req.va_data.amount

    # Get collection history
    collections = (
        db.query(Collection)
        .filter(Collection.customer_id == customer_id)
        .order_by(Collection.timestamp.desc())
        .limit(20)
        .all()
    )

    agent = customer.agent

    return CustomerDetailResponse(
        id=customer.id,
        name=customer.name,
        address=customer.address,
        phone=customer.phone,
        lat=customer.lat,
        lng=customer.lng,
        status=customer.status,
        notes=customer.notes,
        assigned_agent_id=customer.assigned_agent_id,
        created_at=customer.created_at,
        agent_name=agent.name if agent else None,
        va_number=va_number,
        va_bank=va_bank,
        va_amount=va_amount,
        va_request_status=va_request_status,
        collections=[CollectionBriefResponse.model_validate(c) for c in collections],
    )
