from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, case
from typing import Optional, List
from core.database import get_db
from core.dependencies import get_current_user_api
from models.user import User
from models.customer import Customer
from models.collection import Collection
from models.va_request import VaRequest
from models.va_data import VaData
from schemas.customer import CustomerResponse, CustomerDetailResponse, CollectionBriefResponse, PaginatedCustomerResponse, CustomerStats

router = APIRouter(prefix="/api/customers", tags=["Customer API"])

@router.get("", response_model=PaginatedCustomerResponse)
def list_customers(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0),
    pinned_ids: List[int] = Query([]),
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """List customers assigned to current agent with pagination, search, and global stats."""
    base_query = db.query(Customer).filter(Customer.assigned_agent_id == user.id, Customer.is_deleted == 0)

    # Calculate global stats FOR THIS AGENT
    stats = CustomerStats(
        total=base_query.count(),
        bayar=base_query.filter(Customer.status == 'bayar').count(),
        janji_bayar=base_query.filter(Customer.status == 'janji_bayar').count(),
        belum=base_query.filter(Customer.status == 'belum').count(),
        tidak_ketemu=base_query.filter(Customer.status == 'tidak_ketemu').count(),
    )

    # Apply filters for the list
    list_query = base_query
    if status:
        list_query = list_query.filter(Customer.status == status)
    
    if search:
        search_filter = f"%{search}%"
        list_query = list_query.filter(
            or_(
                Customer.name.ilike(search_filter),
                Customer.phone.ilike(search_filter),
                Customer.loan_number.ilike(search_filter)
            )
        )

    # Calculate total matching items for pagination
    total_count = list_query.count()

    # Sort: Pinned first, then Name
    order_stmt = []
    if pinned_ids:
        # Priority for items in pinned_ids
        order_stmt.append(case((Customer.id.in_(pinned_ids), 0), else_=1))
    
    order_stmt.append(Customer.name.asc())

    customers = list_query.order_by(*order_stmt).offset(offset).limit(limit).all()
    
    return PaginatedCustomerResponse(
        customers=[CustomerResponse.model_validate(c) for c in customers],
        stats=stats,
        total_count=total_count
    )


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    customer_id: int,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Get customer detail with VA info and collection history."""
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.assigned_agent_id == user.id, Customer.is_deleted == 0)
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
