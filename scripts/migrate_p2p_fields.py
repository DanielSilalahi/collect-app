import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def migrate():
    columns = [
        "loan_number VARCHAR(100)",
        "platform_name VARCHAR(100)",
        "outstanding_amount FLOAT",
        "due_date DATETIME",
        "overdue_days INTEGER",
        "emergency_contact_1_name VARCHAR(255)",
        "emergency_contact_1_phone VARCHAR(50)",
        "emergency_contact_2_name VARCHAR(255)",
        "emergency_contact_2_phone VARCHAR(50)"
    ]

    with engine.begin() as conn:
        for col in columns:
            try:
                conn.execute(text(f"ALTER TABLE customers ADD COLUMN {col}"))
                print(f"[OK] Added column: {col}")
            except Exception as e:
                # Typically implies column already exists
                print(f"[SKIP] {col} (Might already exist)")

if __name__ == '__main__':
    print("Starting migration for P2P fields...")
    migrate()
    print("Migration finished.")
