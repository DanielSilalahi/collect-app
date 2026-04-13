import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def migrate():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE va_requests ADD COLUMN is_notified_to_agent INTEGER DEFAULT 0"))
            print("[OK] Added column is_notified_to_agent to va_requests")
        except Exception as e:
            # Typically implies column already exists
            print(f"[SKIP] is_notified_to_agent (Might already exist). Error: {str(e)}")

if __name__ == '__main__':
    print("Starting migration for VA notifications...")
    migrate()
    print("Migration finished.")
