from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from core.database import get_db
from core.templates import templates
from models.user import User
from models.customer import Customer
from models.collection import Collection
from models.va_request import VaRequest
from models.activity_log import ActivityLog
import pytz

router = APIRouter(tags=["Dashboard"])


@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    """Redirect root to dashboard."""
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse, name="dashboard")
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    """Dashboard overview page."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user or current_user.role != "admin":
        return RedirectResponse("/login", status_code=302)

    jakarta = pytz.timezone("Asia/Jakarta")
    today = datetime.now(jakarta).date()

    # Stats
    total_customers = db.query(func.count(Customer.id)).filter(Customer.is_deleted == 0).scalar() or 0
    total_agents = db.query(func.count(User.id)).filter(User.role == "agent", User.is_active == True).scalar() or 0

    # Collection hari ini
    collections_today = (
        db.query(func.count(Collection.id))
        .filter(func.date(Collection.timestamp) == today)
        .scalar() or 0
    )

    # Pending VA requests
    pending_va = (
        db.query(func.count(VaRequest.id))
        .filter(VaRequest.status == "pending")
        .scalar() or 0
    )

    # Customer status breakdown
    status_counts = dict(
        db.query(Customer.status, func.count(Customer.id))
        .filter(Customer.is_deleted == 0)
        .group_by(Customer.status)
        .all()
    )
    belum = status_counts.get("belum", 0) + status_counts.get("new", 0)
    janji_bayar = status_counts.get("janji_bayar", 0)
    bayar = status_counts.get("bayar", 0)
    tidak_ketemu = status_counts.get("tidak_ketemu", 0)

    # Recent activity
    recent_logs = (
        db.query(ActivityLog)
        .join(User, User.id == ActivityLog.user_id)
        .order_by(ActivityLog.timestamp.desc())
        .limit(15)
        .all()
    )

    # For each log, attach user name
    log_items = []
    for log in recent_logs:
        user_obj = db.query(User).filter(User.id == log.user_id).first()
        log_items.append({
            "user_name": user_obj.name if user_obj else "Unknown",
            "action": log.action,
            "detail": log.detail,
            "timestamp": log.timestamp,
        })

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "current_user": current_user,
            "total_customers": total_customers,
            "total_agents": total_agents,
            "collections_today": collections_today,
            "pending_va": pending_va,
            "belum": belum,
            "janji_bayar": janji_bayar,
            "bayar": bayar,
            "tidak_ketemu": tidak_ketemu,
            "recent_logs": log_items,
        },
    )
