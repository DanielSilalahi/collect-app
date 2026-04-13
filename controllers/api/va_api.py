from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user_api
from models.user import User
from models.customer import Customer
from models.va_request import VaRequest
from models.va_data import VaData
from models.activity_log import ActivityLog
from schemas.va import VaRequestCreate, VaRequestResponse

router = APIRouter(prefix="/api/va", tags=["VA API"])


@router.post("/request", response_model=VaRequestResponse)
def request_va(
    payload: VaRequestCreate,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Agent requests a VA for a customer."""
    customer = db.query(Customer).filter(
        Customer.id == payload.customer_id,
        Customer.assigned_agent_id == user.id,
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")

    # Check if there's already an active VA request
    existing = (
        db.query(VaRequest)
        .filter(
            VaRequest.customer_id == payload.customer_id,
            VaRequest.status == "pending",
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Customer sudah memiliki VA request yang pending")

    # Check if customer already has active VA
    completed_with_va = (
        db.query(VaRequest)
        .join(VaData, VaData.va_request_id == VaRequest.id)
        .filter(
            VaRequest.customer_id == payload.customer_id,
            VaRequest.status == "completed",
        )
        .first()
    )
    if completed_with_va:
        raise HTTPException(status_code=400, detail="Customer sudah memiliki VA aktif")

    va_request = VaRequest(
        customer_id=payload.customer_id,
        agent_id=user.id,
        notes=payload.notes,
        status="pending",
    )
    db.add(va_request)

    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action="request_va",
        detail=f"VA request untuk customer #{customer.id} ({customer.name})",
    )
    db.add(log)
    db.commit()
    db.refresh(va_request)

    return VaRequestResponse(
        id=va_request.id,
        customer_id=va_request.customer_id,
        agent_id=va_request.agent_id,
        notes=va_request.notes,
        status=va_request.status,
        created_at=va_request.created_at,
    )


@router.get("/{customer_id}", response_model=VaRequestResponse)
def get_va(
    customer_id: int,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Get VA data for a customer."""
    va_request = (
        db.query(VaRequest)
        .filter(VaRequest.customer_id == customer_id)
        .order_by(VaRequest.created_at.desc())
        .first()
    )
    if not va_request:
        raise HTTPException(status_code=404, detail="Tidak ada VA request untuk customer ini")

    va_number = None
    va_bank = None
    va_amount = None

    if va_request.va_data:
        va_number = va_request.va_data.va_number
        va_bank = va_request.va_data.bank_name
        va_amount = va_request.va_data.amount

    return VaRequestResponse(
        id=va_request.id,
        customer_id=va_request.customer_id,
        agent_id=va_request.agent_id,
        notes=va_request.notes,
        status=va_request.status,
        created_at=va_request.created_at,
        va_number=va_number,
        va_bank=va_bank,
        va_amount=va_amount,
    )

@router.get("/notifications/pending")
def get_pending_notifications(
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Get completed VA requests that haven't been notified to the agent yet."""
    pending_notifs = (
        db.query(VaRequest)
        .filter(
            VaRequest.agent_id == user.id,
            VaRequest.status == "completed",
            VaRequest.is_notified_to_agent == 0
        )
        .all()
    )
    
    results = []
    for req in pending_notifs:
        results.append({
            "id": req.id,
            "customer_id": req.customer_id,
            "customer_name": req.customer.name if req.customer else "Nasabah",
            "va_number": req.va_data.va_number if req.va_data else None,
            "bank_name": req.va_data.bank_name if req.va_data else None,
        })
        
    return results

@router.post("/{va_request_id}/mark-notified")
def mark_notified(
    va_request_id: int,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Mark a VA request as successfully notified on the agent's device."""
    va_req = db.query(VaRequest).filter(
        VaRequest.id == va_request_id,
        VaRequest.agent_id == user.id
    ).first()
    
    if not va_req:
        raise HTTPException(status_code=404, detail="VA request tidak ditemukan")
        
    va_req.is_notified_to_agent = 1
    db.commit()
    return {"success": True}
