from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import verify_password
from core.templates import templates
from models.user import User
from models.activity_log import ActivityLog

router = APIRouter(tags=["Dashboard Auth"])


@router.get("/login", response_class=HTMLResponse, name="login")
def login_page(request: Request):
    """Render login page."""
    # If already logged in, redirect to dashboard
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process login form."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "Username atau password salah"},
            status_code=401,
        )
    if not user.is_active:
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "Akun nonaktif"},
            status_code=403,
        )
    if user.role != "admin":
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "Hanya admin yang bisa login ke dashboard"},
            status_code=403,
        )

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role

    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action="login",
        detail="Login via dashboard",
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()

    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout", name="logout")
def logout(request: Request):
    """Clear session and redirect to login."""
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
