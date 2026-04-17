import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from core.config import settings
from core.database import init_db, SessionLocal
from core.security import hash_password
from core.templates import templates
from models.user import User

# Import API controllers
from controllers.api import auth_api, customer_api, collection_api, va_api, visit_status_api

# Import dashboard controllers
from controllers.dashboard import (
    auth_controller,
    dashboard_controller,
    customer_controller,
    va_controller,
    activity_controller,
    user_controller,
    collection_controller,
    setting_controller,
)

app = FastAPI(title="Collection System P2P", version="1.0.0", debug=True)

# Session middleware for dashboard
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    max_age=60 * 60 * 8,  # 8 hours
    same_site="lax",
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register API routes
app.include_router(auth_api.router)
app.include_router(customer_api.router)
app.include_router(collection_api.router)
app.include_router(va_api.router)
app.include_router(visit_status_api.router)

# Register dashboard routes
app.include_router(auth_controller.router)
app.include_router(dashboard_controller.router)
app.include_router(customer_controller.router)
app.include_router(va_controller.router)
app.include_router(activity_controller.router)
app.include_router(user_controller.router)
app.include_router(collection_controller.router)
app.include_router(setting_controller.router)

# 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return templates.TemplateResponse(request, "404.html", status_code=404)


@app.on_event("startup")
def on_startup():
    """Initialize database and seed admin user."""
    import os
    if os.getenv("DISABLE_AUTO_SEED") == "1":
        return
        
    init_db()

    # Seed default admin user if none exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            admin = User(
                name="Administrator",
                username="admin",
                password=hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(admin)

            # Also create a demo agent
            agent = User(
                name="Agent Demo",
                username="agent1",
                password=hash_password("agent123"),
                role="agent",
                phone="08123456789",
                is_active=True,
            )
            db.add(agent)
            db.commit()
            print("[OK] Default admin (admin/admin123) and agent (agent1/agent123) created")
    finally:
        db.close()


# Suppress static file logs
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/static/" not in record.getMessage() and "/uploads/" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
