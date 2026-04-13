from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from core.jwt import verify_token
from models.user import User

security_scheme = HTTPBearer()


def get_current_user_api(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract user from JWT Bearer token — used by REST API endpoints."""
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token tidak valid atau kadaluarsa")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User tidak ditemukan atau nonaktif")
    return user


def get_current_agent(user: User = Depends(get_current_user_api)) -> User:
    """Ensure current API user is an agent."""
    if user.role != "agent":
        raise HTTPException(status_code=403, detail="Hanya agent yang bisa mengakses")
    return user


def get_admin_session(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract admin user from session cookie — used by dashboard."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.role != "admin":
        return None
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """Require admin session — redirect to login if not authenticated."""
    user = get_admin_session(request, db)
    if user is None:
        from fastapi.responses import RedirectResponse
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user
