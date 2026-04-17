from core.database import engine
from sqlalchemy import text, inspect

def migrate():
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("field_settings")]
        
        if "category_id" not in columns:
            print("Adding category_id column...")
            conn.execute(text("ALTER TABLE field_settings ADD COLUMN category_id INT"))
            conn.commit()
            print("Column added.")
        else:
            print("Column already exists.")

if __name__ == "__main__":
    migrate()
