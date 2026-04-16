import os
import sys

from sqlalchemy import text

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, engine


SNAPSHOT_COLUMNS = [
    "full_name VARCHAR(255)",
    "nick_name VARCHAR(100)",
    "customer_code VARCHAR(100)",
    "external_customer_id VARCHAR(100)",
    "primary_phone VARCHAR(50)",
    "primary_city VARCHAR(100)",
    "primary_address_summary TEXT",
    "sub_status VARCHAR(50)",
    "current_loan_id INTEGER",
    "current_dpd INTEGER",
    "current_total_outstanding NUMERIC(18,2)",
    "last_payment_date DATE",
    "last_payment_amount NUMERIC(18,2)",
    "last_contacted_at DATETIME",
    "search_name VARCHAR(255)",
    "search_nik VARCHAR(50)",
]


def add_missing_customer_columns(conn):
    for column_sql in SNAPSHOT_COLUMNS:
        try:
            conn.execute(text(f"ALTER TABLE customers ADD COLUMN {column_sql}"))
            print(f"[OK] Added column: {column_sql}")
        except Exception:
            print(f"[SKIP] {column_sql}")


def migrate():
    from models import customer_address, customer_contact, customer_import_row, customer_loan  # noqa: F401

    Base.metadata.create_all(engine, checkfirst=True)
    with engine.begin() as conn:
        add_missing_customer_columns(conn)


if __name__ == "__main__":
    print("Starting migration for customer semi-normalized fields...")
    migrate()
    print("Migration finished.")
