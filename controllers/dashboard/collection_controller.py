import math
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.templates import templates
from core.utils.export_helper import DataExporter
from models.user import User
from models.collection import Collection

router = APIRouter(tags=["Collection Management"])


def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    return user


@router.get("/collections", response_class=HTMLResponse, name="collections")
def collection_list(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    status: str = Query(default=None),
    agent_id: str = Query(default=None),
):
    """Collections list page."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    per_page = 20
    query = (
        db.query(Collection)
        .options(
            joinedload(Collection.customer),
            joinedload(Collection.agent),
        )
    )

    if status:
        query = query.filter(Collection.status == status)
    if agent_id and agent_id.isdigit():
        query = query.filter(Collection.agent_id == int(agent_id))

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    if page > total_pages:
        page = total_pages

    collections = (
        query.order_by(Collection.timestamp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    agents = db.query(User).filter(User.role == "agent", User.is_active == True).all()

    return templates.TemplateResponse(
        request,
        "collections/list.html",
        {
            "current_user": current_user,
            "collections": collections,
            "agents": agents,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "status_filter": status,
            "agent_filter": agent_id,
        },
    )


@router.get("/collections/export")
def export_collections(
    request: Request,
    status: str = Query(default=None),
    agent_id: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """Export collections to Excel."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    query = (
        db.query(Collection)
        .options(
            joinedload(Collection.customer),
            joinedload(Collection.agent),
        )
    )

    if status:
        query = query.filter(Collection.status == status)
    if agent_id and agent_id.isdigit():
        query = query.filter(Collection.agent_id == int(agent_id))

    query = query.order_by(Collection.timestamp.desc())

    field_mappings = [
        {"label": "ID", "attr": "id"},
        {"label": "Customer", "attr": "customer.full_name"},
        {"label": "Agent", "attr": "agent.name"},
        {"label": "Status", "attr": "status"},
        {"label": "Notes", "attr": "notes"},
        {"label": "GPS Lat", "attr": "gps_lat"},
        {"label": "GPS Lng", "attr": "gps_lng"},
        {"label": "Timestamp", "func": lambda x: DataExporter.format_datetime(x.timestamp)},
    ]

    return DataExporter.export_to_excel(
        query=query,
        field_mappings=field_mappings,
        filename_prefix="collections",
        sheet_title="Collections"
    )
