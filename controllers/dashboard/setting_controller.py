from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from core.database import get_db
from models.field_setting import FieldSetting
from models.field_category import FieldCategory
from models.user import User
from models.activity_log import ActivityLog
from models.visit_status import VisitStatus
from fastapi.templating import Jinja2Templates
from urllib.parse import quote
from controllers.dashboard.customer_controller import UPLOAD_FIELD_DEFINITIONS

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    return user

@router.get("/settings/excel", response_class=HTMLResponse)
def setting_excel_mapping(
    request: Request,
    db: Session = Depends(get_db),
):
    """Manage dynamic field settings for Excel mapping."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    # Fetch categories
    categories = db.query(FieldCategory).all()
    
    # Fetch existing settings
    settings_db = db.query(FieldSetting).all()
    settings_map = {s.field_key: s for s in settings_db}

    # Enhance field definitions with DB values
    enhanced_fields = []
    for field in UPLOAD_FIELD_DEFINITIONS:
        f = field.copy()
        db_setting = settings_map.get(field["key"])
        f["display_order"] = db_setting.display_order if db_setting else 100
        f["category_id"] = db_setting.category_id if db_setting else None
        enhanced_fields.append(f)

    # Sort: put identity fields at top of the settings list too if you want, or just by category
    enhanced_fields.sort(key=lambda x: (x["category_id"] or 999, x["display_order"], x["label"]))

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request,
        "settings/excel_settings.html",
        {
            "current_user": current_user,
            "fields": enhanced_fields,
            "categories": categories,
            "success": success,
            "error": error,
            "active_page": "settings"
        },
    )

@router.post("/settings/excel/save")
async def save_excel_mapping_settings(
    request: Request,
    db: Session = Depends(get_db),
):
    """Save field mapping preferences."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    form_data = await request.form()
    all_keys = {f["key"] for f in UPLOAD_FIELD_DEFINITIONS}
    
    for key in all_keys:
        cat_id_raw = form_data.get(f"category_{key}")
        cat_id = int(cat_id_raw) if cat_id_raw and cat_id_raw.isdigit() else None
        
        setting = db.query(FieldSetting).filter(FieldSetting.field_key == key).first()
        if not setting:
            setting = FieldSetting(field_key=key, category_id=cat_id)
            db.add(setting)
        else:
            setting.category_id = cat_id

    db.commit()
    return RedirectResponse(f"/settings/excel?success={quote('Pengaturan mapping berhasil disimpan')}", status_code=302)

# --- Category Management ---

@router.get("/settings/excel/categories", response_class=HTMLResponse)
def manage_categories(request: Request, db: Session = Depends(get_db)):
    current_user = _require_admin(request, db)
    if not current_user: return RedirectResponse("/login", status_code=302)
    
    categories = db.query(FieldCategory).order_by(FieldCategory.is_system.desc(), FieldCategory.id).all()
    return templates.TemplateResponse(request, "settings/excel_categories.html", {
        "current_user": current_user,
        "categories": categories,
        "active_page": "settings",
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error")
    })

@router.post("/settings/excel/categories/save")
async def save_category(request: Request, db: Session = Depends(get_db)):
    current_user = _require_admin(request, db)
    if not current_user: return RedirectResponse("/login", status_code=302)
    
    form_data = await request.form()
    cat_id = form_data.get("id")
    name = form_data.get("label")
    description = form_data.get("description")
    icon = form_data.get("icon", "bi-folder")
    
    if cat_id:
        cat = db.query(FieldCategory).get(int(cat_id))
        if cat:
            cat.label = name
            cat.description = description
            cat.icon = icon
    else:
        # Generate key from name
        key = name.lower().replace(" ", "_")
        cat = FieldCategory(key=key, label=name, description=description, icon=icon)
        db.add(cat)
    
    db.commit()
    return RedirectResponse(f"/settings/excel/categories?success={quote('Kategori berhasil disimpan')}", status_code=302)

@router.post("/settings/excel/categories/delete/{cat_id}")
def delete_category(cat_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = _require_admin(request, db)
    if not current_user: return RedirectResponse("/login", status_code=302)
    
    cat = db.query(FieldCategory).get(cat_id)
    if cat and not cat.is_system:
        # Move fields in this category to None/Uncategorized
        db.query(FieldSetting).filter(FieldSetting.category_id == cat_id).update({"category_id": None})
        db.delete(cat)
        db.commit()
        return RedirectResponse(f"/settings/excel/categories?success={quote('Kategori berhasil dihapus')}", status_code=302)
    
    return RedirectResponse(f"/settings/excel/categories?error={quote('Kategori sistem tidak bisa dihapus')}", status_code=302)

# --- Visit Status Management ---

@router.get("/settings/visit-statuses", response_class=HTMLResponse)
def manage_visit_statuses(request: Request, db: Session = Depends(get_db)):
    current_user = _require_admin(request, db)
    if not current_user: return RedirectResponse("/login", status_code=302)
    
    statuses = db.query(VisitStatus).order_by(VisitStatus.display_order).all()
    return templates.TemplateResponse(request, "settings/visit_statuses.html", {
        "current_user": current_user,
        "statuses": statuses,
        "active_page": "settings",
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error")
    })

@router.post("/settings/visit-statuses/save")
async def save_visit_status(request: Request, db: Session = Depends(get_db)):
    current_user = _require_admin(request, db)
    if not current_user: return RedirectResponse("/login", status_code=302)
    
    form_data = await request.form()
    status_id = form_data.get("id")
    label = form_data.get("label")
    color_code = form_data.get("color_code", "#10B981")
    icon = form_data.get("icon", "bi-check-circle")
    display_order = int(form_data.get("display_order", 0))
    is_ptp = form_data.get("is_ptp") == "on"
    is_active = form_data.get("is_active") == "on"
    
    if status_id:
        status = db.query(VisitStatus).get(int(status_id))
        if status:
            status.label = label
            status.color_code = color_code
            status.icon = icon
            status.display_order = display_order
            status.is_ptp = is_ptp
            status.is_active = is_active
    else:
        key = label.lower().replace(" ", "_")
        status = VisitStatus(
            key=key, 
            label=label, 
            color_code=color_code, 
            icon=icon, 
            display_order=display_order,
            is_ptp=is_ptp,
            is_active=is_active
        )
        db.add(status)
    
    db.commit()
    return RedirectResponse(f"/settings/visit-statuses?success={quote('Status kunjungan berhasil disimpan')}", status_code=302)

@router.post("/settings/visit-statuses/delete/{status_id}")
def delete_visit_status(status_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = _require_admin(request, db)
    if not current_user: return RedirectResponse("/login", status_code=302)
    
    status = db.query(VisitStatus).get(status_id)
    if status:
        db.delete(status)
        db.commit()
        return RedirectResponse(f"/settings/visit-statuses?success={quote('Status kunjungan berhasil dihapus')}", status_code=302)
    
    return RedirectResponse(f"/settings/visit-statuses?error={quote('Status tidak ditemukan')}", status_code=302)
