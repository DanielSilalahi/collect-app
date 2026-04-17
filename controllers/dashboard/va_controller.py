import math
from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.templates import templates
from core.utils.export_helper import DataExporter
from models.user import User
from models.customer import Customer
from models.va_request import VaRequest
from models.va_data import VaData
from models.activity_log import ActivityLog
from urllib.parse import quote

router = APIRouter(tags=["VA Management"])


def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    return user


@router.get("/va-requests", response_class=HTMLResponse, name="va_requests")
def va_list(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    status: str = Query(default=None),
):
    """VA requests list page."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    per_page = 20
    query = (
        db.query(VaRequest)
        .options(
            joinedload(VaRequest.customer),
            joinedload(VaRequest.agent),
            joinedload(VaRequest.va_data),
        )
    )

    if status:
        query = query.filter(VaRequest.status == status)

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    if page > total_pages:
        page = total_pages

    va_requests = (
        query.order_by(VaRequest.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Counts
    pending_count = db.query(VaRequest).filter(VaRequest.status == "pending").count()
    completed_count = db.query(VaRequest).filter(VaRequest.status == "completed").count()

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request,
        "va/list.html",
        {
            "current_user": current_user,
            "va_requests": va_requests,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "status_filter": status,
            "pending_count": pending_count,
            "completed_count": completed_count,
            "success": success,
            "error": error,
        },
    )


@router.post("/va-requests/{va_request_id}/create-va")
def create_va(
    va_request_id: int,
    request: Request,
    va_number: str = Form(...),
    bank_name: str = Form(...),
    amount: int = Form(None),
    db: Session = Depends(get_db),
):
    """Admin creates VA data for a request."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    va_request = db.query(VaRequest).filter(VaRequest.id == va_request_id).first()
    if not va_request:
        return RedirectResponse(
            f"/va-requests?error={quote('VA request tidak ditemukan')}",
            status_code=302,
        )

    if va_request.status == "completed":
        return RedirectResponse(
            f"/va-requests?error={quote('VA sudah dibuat sebelumnya')}",
            status_code=302,
        )

    # Create VA data
    va_data = VaData(
        va_request_id=va_request_id,
        va_number=va_number.strip(),
        bank_name=bank_name.strip(),
        amount=amount,
        created_by_admin=current_user.id,
    )
    db.add(va_data)

    # Update request status
    va_request.status = "completed"

    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="create_va",
        detail=f"VA #{va_number} ({bank_name}) untuk request #{va_request_id}",
    )
    db.add(log)
    db.commit()

    return RedirectResponse(
        f"/va-requests?success={quote(f'VA {va_number} berhasil dibuat')}",
        status_code=302,
    )


@router.get("/va-requests/export")
def export_va_requests(
    request: Request,
    status: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """Export VA requests to Excel."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    query = (
        db.query(VaRequest)
        .options(
            joinedload(VaRequest.customer),
            joinedload(VaRequest.agent),
            joinedload(VaRequest.va_data),
        )
    )

    if status:
        query = query.filter(VaRequest.status == status)

    query = query.order_by(VaRequest.created_at.desc())

    field_mappings = [
        {"label": "ID", "attr": "id"},
        {"label": "Customer", "attr": "customer.full_name"},
        {"label": "Agent", "attr": "agent.name"},
        {"label": "Status", "attr": "status"},
        {"label": "VA Number", "attr": "va_data.va_number"},
        {"label": "Bank", "attr": "va_data.bank_name"},
        {"label": "Amount Requested", "attr": "amount"},
        {"label": "Amount Created", "attr": "va_data.amount"},
        {"label": "Requested At", "func": lambda x: DataExporter.format_datetime(x.created_at)},
        {"label": "Created At", "func": lambda x: DataExporter.format_datetime(x.va_data.created_at) if x.va_data else "-"},
    ]

    return DataExporter.export_to_excel(
        query=query,
        field_mappings=field_mappings,
        filename_prefix="va_requests",
        sheet_title="VA Requests"
    )
