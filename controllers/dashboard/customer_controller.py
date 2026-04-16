import io
import math
import re
from urllib.parse import quote
from collections import namedtuple
from datetime import date, datetime

import openpyxl
import pytz
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from core.templates import templates
from models.user import User
from models.customer import Customer
from models.customer_address import CustomerAddress
from models.customer_contact import CustomerContact
from models.customer_import_row import CustomerImportRow
from models.customer_loan import CustomerLoan
from models.activity_log import ActivityLog

router = APIRouter(tags=["Customer Management"])
CustomerImportPayload = namedtuple(
    "CustomerImportPayload",
    ["customer", "loan", "address", "contact", "import_row"],
)


def clean_string(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value or value.lower() == "none":
        return None
    return value


def normalize_text(value):
    cleaned = clean_string(value)
    if not cleaned:
        return None
    lowered = cleaned.lower()
    return re.sub(r"\s+", " ", lowered).strip()


def stringify_value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def parse_int(value):
    value = clean_string(value)
    if value is None:
        return None
    try:
        return int(float(value.replace(",", "")))
    except Exception:
        return None


def parse_float(value):
    value = clean_string(value)
    if value is None:
        return None
    try:
        return float(value.replace(",", ""))
    except Exception:
        return None


def parse_decimal(value):
    parsed = parse_float(value)
    if parsed is None:
        return None
    if float(parsed).is_integer():
        return int(parsed)
    return parsed


def parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = clean_string(value)
    if raw is None:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    return None


def get_val(row, mapping, field_name):
    source_key = mapping.get(field_name)
    if source_key is None:
        return None
    if isinstance(row, dict):
        return row.get(source_key)
    return None


def build_customer_import_payload(row, mapping, batch_code):
    full_name = clean_string(get_val(row, mapping, "full_name"))
    primary_phone = clean_string(get_val(row, mapping, "primary_phone"))
    full_address = clean_string(get_val(row, mapping, "full_address"))
    city = clean_string(get_val(row, mapping, "city"))
    platform_name = clean_string(get_val(row, mapping, "platform_name"))
    raw_lat_lng = clean_string(get_val(row, mapping, "raw_lat_lng"))

    customer = Customer(
        full_name=full_name,
        primary_phone=primary_phone,
        primary_address_summary=full_address,
        primary_city=city,
        platform_name=platform_name,
        assigned_agent_id=None,
        status="new",
        upload_batch=batch_code,
        search_name=normalize_text(full_name),
    )

    loan = CustomerLoan(
        is_current=1,
        loan_number=clean_string(get_val(row, mapping, "loan_number")),
        platform_name=platform_name,
        total_outstanding=parse_decimal(get_val(row, mapping, "total_outstanding")),
        overdue_days=parse_int(get_val(row, mapping, "overdue_days")),
        due_date=parse_date(get_val(row, mapping, "due_date")),
    )

    address = CustomerAddress(
        address_type="home",
        full_address=full_address or "-",
        city=city,
        lat=parse_float(get_val(row, mapping, "lat")),
        lng=parse_float(get_val(row, mapping, "lng")),
        raw_lat_lng=raw_lat_lng,
        is_primary=1,
    )

    emergency_name = clean_string(get_val(row, mapping, "emergency_contact_name"))
    emergency_phone = clean_string(get_val(row, mapping, "emergency_contact_phone"))
    contact = None
    if emergency_name or emergency_phone:
        contact = CustomerContact(
            contact_type="phone",
            contact_role="emergency",
            name=emergency_name,
            phone_number=emergency_phone,
            is_primary=0,
        )

    import_row = CustomerImportRow(
        upload_batch=batch_code,
        import_status="imported",
        raw_customer_name=full_name,
        raw_phone=primary_phone,
        raw_address=full_address,
        raw_city=city,
        raw_due_date=stringify_value(get_val(row, mapping, "due_date")),
        raw_outstanding_amount=stringify_value(get_val(row, mapping, "total_outstanding")),
        raw_overdue_days=stringify_value(get_val(row, mapping, "overdue_days")),
        raw_lat=str(parse_float(get_val(row, mapping, "lat"))) if parse_float(get_val(row, mapping, "lat")) is not None else None,
        raw_lng=str(parse_float(get_val(row, mapping, "lng"))) if parse_float(get_val(row, mapping, "lng")) is not None else None,
        raw_lat_lng=raw_lat_lng,
        raw_platform_name=platform_name,
        raw_payload=dict(row),
    )

    return CustomerImportPayload(
        customer=customer,
        loan=loan,
        address=address,
        contact=contact,
        import_row=import_row,
    )


def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    return user


@router.get("/customers", response_class=HTMLResponse, name="customers")
def customer_list_batches(
    request: Request,
    db: Session = Depends(get_db),
):
    """Customer batch list overview."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    from sqlalchemy import case, func

    batches_query = db.query(
        Customer.upload_batch,
        func.count(Customer.id).label("total_customers"),
        func.sum(case((Customer.assigned_agent_id != None, 1), else_=0)).label("assigned_count"),
        func.max(Customer.created_at).label("upload_date")
    ).filter(Customer.is_deleted == 0).group_by(Customer.upload_batch).order_by(func.max(Customer.created_at).desc()).all()

    agents = db.query(User).filter(User.role == "agent", User.is_active == True).all()

    # Get success/error from query params
    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request,
        "customers/batches.html",
        {
            "current_user": current_user,
            "batches": batches_query,
            "agents": agents,
            "success": success,
            "error": error,
        },
    )

@router.get("/customers/batch/{batch_code}", response_class=HTMLResponse, name="customer_batch_detail")
def customer_batch_detail(
    request: Request,
    batch_code: str,
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    status: str = Query(default=None),
    agent_id: str = Query(default=None),
    search: str = Query(default=None),
):
    """Customer list page for a specific batch."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    per_page = 20
    from sqlalchemy.orm import joinedload
    from models.collection import Collection
    query = db.query(Customer).options(
        joinedload(Customer.collections).joinedload(Collection.agent)
    ).filter(Customer.is_deleted == 0)
    
    if batch_code.lower() == "manual":
        query = query.filter(Customer.upload_batch == None)
    else:
        query = query.filter(Customer.upload_batch == batch_code)

    if status:
        query = query.filter(Customer.status == status)
    if agent_id and agent_id.isdigit():
        query = query.filter(Customer.assigned_agent_id == int(agent_id))
    if search:
        query = query.filter(Customer.full_name.ilike(f"%{search}%"))

    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    if page > total_pages:
        page = total_pages

    customers = (
        query.order_by(Customer.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    agents = db.query(User).filter(User.role == "agent", User.is_active == True).all()

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        request,
        "customers/list.html",
        {
            "current_user": current_user,
            "customers": customers,
            "agents": agents,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "status_filter": status,
            "agent_filter": agent_id,
            "search": search or "",
            "success": success,
            "error": error,
            "batch_code": batch_code
        },
    )


@router.post("/customers/upload")
async def upload_customers(
    request: Request,
    file: UploadFile = File(...),
    agent_id: int = Form(None),
    db: Session = Depends(get_db),
):
    """Step 1: Upload customers from Excel file and show mapping UI."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        return RedirectResponse(
            f"/customers?error={quote('Format file harus .xlsx')}",
            status_code=302,
        )

    try:
        contents = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
        ws = wb.active
        
        # Read the first row to get headers
        headers = []
        for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
            headers = [str(cell).strip() if cell is not None else f"Column_{i}" for i, cell in enumerate(row)]
            break
        
        wb.close()

        if not headers:
            return RedirectResponse(
                f"/customers?error={quote('File kosong atau tidak memiliki header')}",
                status_code=302,
            )

        # Save file temporarily
        import os, uuid
        temp_dir = "static/uploads/temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_filename = f"{uuid.uuid4().hex}.xlsx"
        temp_filepath = os.path.join(temp_dir, temp_filename)
        
        with open(temp_filepath, "wb") as f:
            f.write(contents)

        # Define the expected database fields for mapping
        expected_fields = [
            {"key": "full_name", "label": "Nama (Wajib)", "required": True},
            {"key": "primary_phone", "label": "No. HP Utama", "required": False},
            {"key": "full_address", "label": "Alamat Utama", "required": False},
            {"key": "city", "label": "Kota", "required": False},
            {"key": "loan_number", "label": "Nomor Kontrak / Loan Number", "required": False},
            {"key": "platform_name", "label": "Platform / Aplikasi", "required": False},
            {"key": "total_outstanding", "label": "Outstanding Amount", "required": False},
            {"key": "overdue_days", "label": "Overdue (DPD)", "required": False},
            {"key": "due_date", "label": "Tanggal Jatuh Tempo", "required": False},
            {"key": "raw_lat_lng", "label": "Latitude & Longitude Gabungan", "required": False},
            {"key": "lat", "label": "Latitude (GPS)", "required": False},
            {"key": "lng", "label": "Longitude (GPS)", "required": False},
            {"key": "emergency_contact_name", "label": "Emergency Contact Name", "required": False},
            {"key": "emergency_contact_phone", "label": "Emergency Contact Phone", "required": False},
        ]

        return templates.TemplateResponse(
            request,
            "customers/upload_mapping.html",
            {
                "current_user": current_user,
                "headers": headers,
                "expected_fields": expected_fields,
                "temp_filename": temp_filename,
                "agent_id": agent_id or "",
            },
        )

    except Exception as e:
        return RedirectResponse(
            f"/customers?error={quote(f'Gagal memproses file: {str(e)}')}",
            status_code=302,
        )

@router.post("/customers/upload/process")
async def process_customers_upload(
    request: Request,
    temp_filename: str = Form(...),
    agent_id: str = Form(None),
    db: Session = Depends(get_db),
):
    """Step 2: Process mapping and insert data."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    import os
    temp_filepath = os.path.join("static/uploads/temp", temp_filename)
    if not os.path.exists(temp_filepath):
        return RedirectResponse(
            f"/customers?error={quote('File temporary tidak ditemukan. Silahkan upload ulang.')}",
            status_code=302,
        )

    try:
        form_data = await request.form()
        
        # Get mapping configuration
        # e.g., form_data["mapped_name"] = "0" (index string of the column)
        mapping = {}
        for key in form_data.keys():
            if key.startswith("mapped_"):
                field_name = key.replace("mapped_", "")
                col_idx_str = form_data.get(key)
                if col_idx_str and col_idx_str.isdigit():
                    mapping[field_name] = int(col_idx_str)

        if "full_name" not in mapping:
             return RedirectResponse(
                f"/customers?error={quote('Mapping kolom Nama wajib diisi.')}",
                status_code=302,
             )

        # Parse the actual file
        wb = openpyxl.load_workbook(temp_filepath, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()

        if len(rows) < 2:
            return RedirectResponse(
                f"/customers?error={quote('File kosong')}",
                status_code=302,
            )

        jakarta = pytz.timezone("Asia/Jakarta")
        batch_code = f"UPLOAD_{datetime.now(jakarta).strftime('%Y%m%d_%H%M%S')}"
        count = 0

        agent_id_val = int(agent_id) if agent_id and agent_id.isdigit() else None

        headers = [str(cell).strip() if cell is not None else f"Column_{i}" for i, cell in enumerate(rows[0])]

        for row in rows[1:]:
            if all(v is None for v in row):
                continue

            row_payload = {headers[idx]: row[idx] if idx < len(row) else None for idx in range(len(headers))}
            mapped_headers = {
                field_name: headers[col_idx]
                for field_name, col_idx in mapping.items()
                if col_idx < len(headers)
            }

            payload = build_customer_import_payload(
                row=row_payload,
                mapping=mapped_headers,
                batch_code=batch_code,
            )

            if not payload.customer.full_name:
                continue

            customer = payload.customer
            customer.assigned_agent_id = agent_id_val
            db.add(customer)
            db.flush()

            payload.loan.customer_id = customer.id
            db.add(payload.loan)
            db.flush()

            customer.current_loan_id = payload.loan.id
            customer.current_dpd = payload.loan.overdue_days
            customer.current_total_outstanding = payload.loan.total_outstanding

            payload.address.customer_id = customer.id
            db.add(payload.address)

            if payload.contact:
                payload.contact.customer_id = customer.id
                db.add(payload.contact)

            payload.import_row.customer_id = customer.id
            db.add(payload.import_row)
            count += 1

        # Cleanup
        try:
            os.remove(temp_filepath)
        except:
            pass

        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="upload_customer",
            detail=f"Upload dynamically {count} customers (batch: {batch_code})",
        )
        db.add(log)
        db.commit()

        return RedirectResponse(
            f"/customers?success={quote(f'Berhasil upload {count} customer (batch: {batch_code})')}",
            status_code=302,
        )

    except Exception as e:
        db.rollback()
        return RedirectResponse(
            f"/customers?error={quote(f'Gagal proses data: {str(e)}')}",
            status_code=302,
        )


@router.post("/customers/assign")
def assign_customer(
    request: Request,
    customer_ids: str = Form(...),
    agent_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """Assign customers to an agent."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    ids = [int(x.strip()) for x in customer_ids.split(",") if x.strip().isdigit()]
    if not ids:
        return RedirectResponse(
            f"/customers?error={quote('Tidak ada customer yang dipilih')}",
            status_code=302,
        )

    agent = db.query(User).filter(User.id == agent_id, User.role == "agent").first()
    if not agent:
        return RedirectResponse(
            f"/customers?error={quote('Agent tidak ditemukan')}",
            status_code=302,
        )

    updated = (
        db.query(Customer)
        .filter(Customer.id.in_(ids))
        .update({"assigned_agent_id": agent_id}, synchronize_session="fetch")
    )

    log = ActivityLog(
        user_id=current_user.id,
        action="assign_customer",
        detail=f"Assign {updated} customers ke agent {agent.name}",
    )
    db.add(log)
    db.commit()

    referer = request.headers.get("referer") or "/customers"
    if "?" in referer:
        referer = referer.split("?")[0]

    return RedirectResponse(
        f"{referer}?success={quote(f'Berhasil assign {updated} customer ke {agent.name}')}",
        status_code=302,
    )


@router.post("/customers/bulk-delete")
def bulk_delete_customers(
    request: Request,
    customer_ids: str = Form(...),
    db: Session = Depends(get_db),
):
    """Bulk delete customers."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    ids = [int(x.strip()) for x in customer_ids.split(",") if x.strip().isdigit()]
    if not ids:
        return RedirectResponse(
            f"/customers?error={quote('Tidak ada customer yang dipilih untuk dihapus')}",
            status_code=302,
        )

    updated = (
        db.query(Customer)
        .filter(Customer.id.in_(ids))
        .update({"is_deleted": 1}, synchronize_session="fetch")
    )

    log = ActivityLog(
        user_id=current_user.id,
        action="delete_bulk_customer",
        detail=f"Menghapus secara lembut (soft delete) {updated} customers",
    )
    db.add(log)
    db.commit()

    referer = request.headers.get("referer") or "/customers"
    if "?" in referer:
        referer = referer.split("?")[0]

    return RedirectResponse(
        f"{referer}?success={quote(f'Berhasil menghapus {deleted_count} data customer')}",
        status_code=302,
    )


@router.post("/customers/batch/{batch_code}/delete")
def delete_batch(
    request: Request,
    batch_code: str,
    db: Session = Depends(get_db),
):
    """Delete all customers in a batch."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    updated = (
        db.query(Customer)
        .filter(Customer.upload_batch == batch_code)
        .update({"is_deleted": 1}, synchronize_session="fetch")
    )

    log = ActivityLog(
        user_id=current_user.id,
        action="delete_batch",
        detail=f"Hapus batch (soft delete) {batch_code} ({updated} customers)",
    )
    db.add(log)
    db.commit()

    return RedirectResponse(
        f"/customers?success={quote(f'Batch {batch_code} dan {count} data di dalamnya berhasil dihapus')}",
        status_code=302,
    )


@router.post("/customers/{customer_id}/delete")
def delete_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a customer."""
    current_user = _require_admin(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return RedirectResponse(
            f"/customers?error={quote('Customer tidak ditemukan')}",
            status_code=302,
        )

    name = customer.full_name
    customer.is_deleted = 1

    log = ActivityLog(
        user_id=current_user.id,
        action="delete_customer",
        detail=f"Hapus customer (soft delete): {name}",
    )
    db.add(log)
    db.commit()

    referer = request.headers.get("referer") or "/customers"
    if "?" in referer:
        referer = referer.split("?")[0]

    return RedirectResponse(
        f"{referer}?success={quote(f'Customer {name} berhasil dihapus')}",
        status_code=302,
    )
