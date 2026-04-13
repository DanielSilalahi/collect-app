from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import verify_password
from core.jwt import create_access_token
from core.dependencies import get_current_user_api
from models.user import User
from models.activity_log import ActivityLog
from schemas.user import LoginRequest, TokenResponse, UserResponse, UpdateFcmTokenRequest

router = APIRouter(prefix="/api/auth", tags=["Auth API"])


@router.post("/login", response_model=TokenResponse)
def api_login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Agent login — returns JWT token."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Username atau password salah")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun nonaktif")

    token = create_access_token({"sub": str(user.id), "role": user.role})

    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action="login",
        detail=f"Login via mobile app",
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def api_me(user: User = Depends(get_current_user_api)):
    """Get current user info."""
    return UserResponse.model_validate(user)


@router.put("/fcm-token")
def update_fcm_token(
    payload: UpdateFcmTokenRequest,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Update FCM token for push notifications."""
    user.fcm_token = payload.fcm_token
    db.commit()
    return {"message": "FCM token updated"}
