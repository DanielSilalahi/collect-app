from core.database import SessionLocal, init_db
from models.field_category import FieldCategory
from models.field_setting import FieldSetting
import sys
import os

# Add parent dir to path so we can import from backend
sys.path.append(os.getcwd())

def seed_categories():
    db = SessionLocal()
    try:
        # 1. Define Categories from CATEGORY_META
        CATEGORY_META = {
            "identity": {
                "label": "Identitas Utama",
                "icon": "bi-person-vcard",
                "description": "Field yang Anda tandai sebagai prioritas untuk identitas dan pencarian dasar.",
                "is_system": True
            },
            "identity_other": {
                "label": "Detail Identitas Lainnya",
                "icon": "bi-person-badge",
                "description": "Informasi identitas tambahan (opsional) yang tidak ditandai sebagai prioritas.",
                "is_system": False
            },
            "location": {
                "label": "Alamat & Lokasi",
                "icon": "bi-geo-alt",
                "description": "Alamat utama, detail domisili, dan koordinat lokasi yang terkait customer.",
                "is_system": False
            },
            "loan": {
                "label": "Pinjaman Aktif",
                "icon": "bi-cash-coin",
                "description": "Field bisnis untuk pinjaman saat ini, outstanding, DPD, pembayaran, dan status collection.",
                "is_system": False
            },
            "contact": {
                "label": "Kontak Tambahan",
                "icon": "bi-telephone-forward",
                "description": "Kontak darurat atau kontak lain yang berhubungan dengan customer.",
                "is_system": False
            },
            "import_meta": {
                "label": "Metadata Import",
                "icon": "bi-archive",
                "description": "Metadata partner dan raw field yang disimpan untuk audit hasil upload.",
                "is_system": False
            },
        }

        # Ensure tables exist
        init_db()

        # 2. Create Categories
        cat_map = {}
        for key, meta in CATEGORY_META.items():
            cat = db.query(FieldCategory).filter(FieldCategory.key == key).first()
            if not cat:
                cat = FieldCategory(
                    key=key,
                    label=meta["label"],
                    icon=meta["icon"],
                    description=meta["description"],
                    is_system=meta["is_system"]
                )
                db.add(cat)
                db.flush()
            cat_map[key] = cat.id
            print(f"Category '{key}' (ID: {cat.id}) ready.")

        # 3. Import UPLOAD_FIELD_DEFINITIONS to assign all fields to categories
        from controllers.dashboard.customer_controller import UPLOAD_FIELD_DEFINITIONS
        
        # We need to know which ones were priority before
        # (Though we can just keep them as is if they already exist)
        
        for field in UPLOAD_FIELD_DEFINITIONS:
            key = field["key"]
            # Map original category to our new category_id
            # Note: identity fields that are not priority should go to identity_other
            # But the logic in customer_controller will handle that during grouping.
            # For now, just assign them to their "original" category key.
            original_cat_key = field["category"]
            cat_id = cat_map.get(original_cat_key)
            
            setting = db.query(FieldSetting).filter(FieldSetting.field_key == key).first()
            if not setting:
                # Default priorities
                is_prio = key in {"full_name", "nik", "primary_phone", "loan_number", "total_outstanding", "overdue_days"}
                setting = FieldSetting(field_key=key, category_id=cat_id, is_priority=is_prio)
                db.add(setting)
            else:
                setting.category_id = cat_id
        
        db.commit()
        print("Success: All categories seeded and fields linked.")

    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_categories()
