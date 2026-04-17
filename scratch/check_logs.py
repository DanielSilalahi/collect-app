from core.database import SessionLocal
from models.activity_log import ActivityLog
from models.user import User

def check_logs():
    db = SessionLocal()
    try:
        logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(20).all()
        for l in logs:
            user = db.query(User).get(l.user_id) if l.user_id else None
            username = user.username if user else "Unknown"
            print(f"[{l.timestamp}] User: {username}, Action: {l.action}, Detail: {l.detail}")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()
