from core.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Making customer_id nullable in va_requests...")
        # Note: syntax might vary depending on DB, assuming MariaDB/MySQL
        try:
            conn.execute(text("ALTER TABLE va_requests MODIFY customer_id INT NULL"))
            conn.commit()
            print("Successfully made customer_id nullable.")
        except Exception as e:
            print(f"Error (might be already nullable or different DB): {e}")

if __name__ == "__main__":
    migrate()
