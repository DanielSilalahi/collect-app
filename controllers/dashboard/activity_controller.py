import math
import io
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from core.database import get_db
from core.templates import templates
from models.user import User
from models.activity_log import ActivityLog
import openpyxl
import pytz

router = APIRouter(tags=["Activity Logs"])


def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    return user


@router.get("/activity-logs", response_class=HTMLResponse, name="activity_logs")
def activity_list(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    action: str = Query(default=None),
    user_id: str = Query(default=None),
):
    """Activity logs list page."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    per_page = 15
    query = db.query(ActivityLog).options(joinedload(ActivityLog.user))

    if action:
        query = query.filter(ActivityLog.action == action)
    if user_id and user_id.isdigit():
        query = query.filter(ActivityLog.user_id == int(user_id))

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    if page > total_pages:
        page = total_pages

    logs = (
        query.order_by(ActivityLog.timestamp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    users = db.query(User).filter(User.is_active == True).all()

    # Distinct action types
    action_types = [
        r[0] for r in db.query(ActivityLog.action).distinct().all()
    ]

    return templates.TemplateResponse(
        request,
        "activity/list.html",
        {
            "current_user": current_user,
            "logs": logs,
            "users": users,
            "action_types": action_types,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "action_filter": action,
            "user_filter": user_id,
        },
    )


@router.get("/activity-logs/export")
def export_activity(
    request: Request,
    db: Session = Depends(get_db),
    action: str = Query(default=None),
    user_id: str = Query(default=None),
):
    """Export activity logs to Excel."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    query = db.query(ActivityLog).options(joinedload(ActivityLog.user))
    if action:
        query = query.filter(ActivityLog.action == action)
    if user_id and user_id.isdigit():
        query = query.filter(ActivityLog.user_id == int(user_id))

    logs = query.order_by(ActivityLog.timestamp.desc()).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Activity Logs"

    # Header
    headers = ["No", "User", "Action", "Detail", "IP Address", "Timestamp"]
    ws.append(headers)

    jakarta = pytz.timezone("Asia/Jakarta")
    for i, log in enumerate(logs, 1):
        ts = log.timestamp
        if ts:
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
        ws.append([
            i,
            log.user.name if log.user else "-",
            log.action,
            log.detail or "-",
            log.ip_address or "-",
            ts or "-",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"activity_logs_{datetime.now(jakarta).strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
