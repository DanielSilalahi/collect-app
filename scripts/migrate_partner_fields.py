import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def migrate():
    # List of columns to add to the customers table
    columns = [
        "partner_name VARCHAR(100)",
        "nik VARCHAR(100)",
        "birth_date DATE",
        "gender VARCHAR(20)",
        "email VARCHAR(255)",
        "updated_at DATETIME"
    ]

    with engine.begin() as conn:
        for col_sql in columns:
            col_name = col_sql.split(" ")[0]
            try:
                conn.execute(text(f"ALTER TABLE customers ADD COLUMN {col_sql}"))
                print(f"[OK] Added column: {col_sql}")
            except Exception as e:
                # Column might already exist
                print(f"[SKIP] {col_name} (details: {str(e)})")

        # Add indexes for the new columns as per the model
        indexes = [
            "ix_customers_partner_name",
            "ix_customers_nik"
        ]
        
        for idx in indexes:
            col_name = idx.replace("ix_customers_", "")
            try:
                conn.execute(text(f"CREATE INDEX {idx} ON customers ({col_name})"))
                print(f"[OK] Created index: {idx}")
            except Exception as e:
                print(f"[SKIP] Index {idx} (details: {str(e)})")

if __name__ == '__main__':
    print("Starting migration for partner and missing fields...")
    migrate()
    print("Migration finished.")
