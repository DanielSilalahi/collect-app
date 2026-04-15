import sys
import os
from sqlalchemy import text

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine

def migrate():
    with engine.begin() as conn:
        try:
            # 1. Add is_deleted column
            conn.execute(text("ALTER TABLE customers ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
            print("[OK] Added column: is_deleted to customers table")
            
            # 2. Add Index for performance
            conn.execute(text("CREATE INDEX ix_customers_is_deleted ON customers (is_deleted)"))
            print("[OK] Created index on is_deleted")
            
        except Exception as e:
            print(f"[SKIP/ERROR] {str(e)}")

if __name__ == '__main__':
    print("Starting migration for Soft Delete field...")
    migrate()
    print("Migration finished.")
