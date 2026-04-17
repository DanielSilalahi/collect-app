from core.database import SessionLocal
from models.field_setting import FieldSetting
from models.field_category import FieldCategory

def sync_priority():
    db = SessionLocal()
    try:
        identity_cat = db.query(FieldCategory).filter(FieldCategory.key == "identity").first()
        if not identity_cat:
            print("Error: Identity category not found.")
            return

        priority_fields = db.query(FieldSetting).filter(FieldSetting.is_priority == True).all()
        for f in priority_fields:
            if f.category_id != identity_cat.id:
                f.category_id = identity_cat.id
                print(f"Updated {f.field_key} to Identity category.")
        
        db.commit()
        print(f"Sync complete. {len(priority_fields)} fields synchronized.")
    finally:
        db.close()

if __name__ == "__main__":
    sync_priority()
