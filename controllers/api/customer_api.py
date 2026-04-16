from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, case
from typing import Optional, List
from sqlalchemy.orm import joinedload, selectinload
from core.database import get_db
from core.dependencies import get_current_user_api
from models.user import User
from models.customer import Customer
from schemas.customer import CustomerAddressResponse, CustomerContactResponse, CustomerDetailResponse, CustomerLoanBriefResponse, CustomerResponse, CollectionBriefResponse, PaginatedCustomerResponse, CustomerStats

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
                Customer.full_name.ilike(search_filter),
                Customer.primary_phone.ilike(search_filter),
                Customer.customer_code.ilike(search_filter)
            )
        )

    # Calculate total matching items for pagination
    total_count = list_query.count()

    # Sort: Pinned first, then Name
    order_stmt = []
    if pinned_ids:
        # Priority for items in pinned_ids
        order_stmt.append(case((Customer.id.in_(pinned_ids), 0), else_=1))
    
    order_stmt.append(Customer.full_name.asc())

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
    """Get customer detail with semi-normalized snapshot and related records."""
    customer = (
        db.query(Customer)
        .options(
            joinedload(Customer.agent),
            joinedload(Customer.current_loan),
            selectinload(Customer.contacts),
            selectinload(Customer.addresses),
            selectinload(Customer.collections),
        )
        .filter(Customer.id == customer_id, Customer.assigned_agent_id == user.id, Customer.is_deleted == 0)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")

    return CustomerDetailResponse(
        id=customer.id,
        full_name=customer.full_name,
        primary_phone=customer.primary_phone,
        primary_city=customer.primary_city,
        primary_address_summary=customer.primary_address_summary,
        platform_name=customer.platform_name,
        status=customer.status,
        sub_status=customer.sub_status,
        current_dpd=customer.current_dpd,
        current_total_outstanding=customer.current_total_outstanding,
        assigned_agent_id=customer.assigned_agent_id,
        created_at=customer.created_at,
        agent_name=customer.agent.name if customer.agent else None,
        current_loan=CustomerLoanBriefResponse.model_validate(customer.current_loan) if customer.current_loan else None,
        contacts=[CustomerContactResponse.model_validate(contact) for contact in customer.contacts],
        addresses=[CustomerAddressResponse.model_validate(address) for address in customer.addresses],
        collections=[
            CollectionBriefResponse.model_validate(collection)
            for collection in sorted(customer.collections, key=lambda item: item.timestamp, reverse=True)[:20]
        ],
    )
