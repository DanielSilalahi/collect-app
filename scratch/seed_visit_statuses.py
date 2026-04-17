from core.database import SessionLocal, engine, Base
from models.visit_status import VisitStatus

def seed_visit_statuses():
    # Ensure table exists
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        defaults = [
            {
                "key": "bayar", 
                "label": "Bayar", 
                "color_code": "#10B981", 
                "icon": "bi-check-circle",
                "display_order": 1
            },
            {
                "key": "janji_bayar", 
                "label": "Janji Bayar", 
                "color_code": "#F59E0B", 
                "icon": "bi-calendar-check",
                "is_ptp": True,
                "display_order": 2
            },
            {
                "key": "tidak_ketemu", 
                "label": "Tidak Ketemu", 
                "color_code": "#EF4444", 
                "icon": "bi-person-x",
                "display_order": 3
            },
            {
                "key": "tidak_di_tempat", 
                "label": "Tidak di Tempat", 
                "color_code": "#6366F1", 
                "icon": "bi-geo",
                "display_order": 4
            },
        ]
        
        for d in defaults:
            exists = db.query(VisitStatus).filter(VisitStatus.key == d["key"]).first()
            if not exists:
                status = VisitStatus(**d)
                db.add(status)
                print(f"Added status: {d['label']}")
        
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_visit_statuses()
