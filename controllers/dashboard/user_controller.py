from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.templates import templates
from core.security import hash_password
from models.user import User
from models.activity_log import ActivityLog
from urllib.parse import quote

router = APIRouter(tags=["User Management"])

def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    return user

@router.get("/users", response_class=HTMLResponse, name="users")
def user_list(
    request: Request,
    db: Session = Depends(get_db),
):
    """User management list page."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    users = db.query(User).order_by(User.id.desc()).all()
    
    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request,
        "users/list.html",
        {
            "current_user": current_user,
            "users": users,
            "success": success,
            "error": error,
            "active_page": "users",
        },
    )

@router.post("/users/add")
def add_user(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    phone: str = Form(None),
    db: Session = Depends(get_db),
):
    """Add a new user/agent."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return RedirectResponse(
            f"/users?error={quote('Username sudah terdaftar')}",
            status_code=302,
        )

    user = User(
        name=name,
        username=username,
        password=hash_password(password),
        role=role,
        phone=phone,
        is_active=True,
    )
    db.add(user)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action="add_user",
        detail=f"Menambahkan {role}: {name} ({username})",
    )
    db.add(log)
    db.commit()

    return RedirectResponse(
        f"/users?success={quote(f'Berhasil menambahkan {role} {name}')}",
        status_code=302,
    )
