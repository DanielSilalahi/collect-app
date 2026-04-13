import io
import math
from urllib.parse import quote
from datetime import datetime

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
from models.activity_log import ActivityLog

router = APIRouter(tags=["Customer Management"])


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
    ).group_by(Customer.upload_batch).order_by(func.max(Customer.created_at).desc()).all()

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
    )
    
    if batch_code.lower() == "manual":
        query = query.filter(Customer.upload_batch == None)
    else:
        query = query.filter(Customer.upload_batch == batch_code)

    if status:
        query = query.filter(Customer.status == status)
    if agent_id and agent_id.isdigit():
        query = query.filter(Customer.assigned_agent_id == int(agent_id))
    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%"))

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
            {"key": "name", "label": "Nama (Wajib)", "required": True},
            {"key": "address", "label": "Alamat", "required": False},
            {"key": "phone", "label": "Phone", "required": False},
            {"key": "loan_number", "label": "Nomor Kontrak / Loan Number", "required": False},
            {"key": "platform_name", "label": "Platform / Aplikasi", "required": False},
            {"key": "outstanding_amount", "label": "Outstanding Amount", "required": False},
            {"key": "overdue_days", "label": "Overdue (DPD)", "required": False},
            {"key": "due_date", "label": "Tanggal Jatuh Tempo (Date)", "required": False},
            {"key": "emergency_contact_1_name", "label": "Emergency Contact 1 (Name)", "required": False},
            {"key": "emergency_contact_1_phone", "label": "Emergency Contact 1 (Phone)", "required": False},
            {"key": "emergency_contact_2_name", "label": "Emergency Contact 2 (Name)", "required": False},
            {"key": "emergency_contact_2_phone", "label": "Emergency Contact 2 (Phone)", "required": False},
            {"key": "lat", "label": "Latitude (GPS)", "required": False},
            {"key": "lng", "label": "Longitude (GPS)", "required": False},
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

        if "name" not in mapping:
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

        for row in rows[1:]:
            if all(v is None for v in row):
                continue
            
            # Extract mapped column values
            def get_val(field):
                if field in mapping:
                    idx = mapping[field]
                    if idx < len(row):
                        return row[idx]
                return None

            name = get_val("name")
            name = str(name).strip() if name is not None else None
            
            if not name or name.lower() == "none":
                continue

            address = get_val("address")
            address = str(address).strip() if address is not None else None
            
            phone = get_val("phone")
            phone = str(phone).strip() if phone is not None else None
            
            loan_number = get_val("loan_number")
            loan_number = str(loan_number).strip() if loan_number is not None else None
            
            platform_name = get_val("platform_name")
            platform_name = str(platform_name).strip() if platform_name is not None else None
            
            # Numeric types
            outstanding_amount = None
            out_val = get_val("outstanding_amount")
            if out_val is not None and str(out_val).strip() != "None":
                try:
                    outstanding_amount = float(str(out_val).replace(',','').strip())
                except:
                    pass

            overdue_days = None
            od_val = get_val("overdue_days")
            if od_val is not None and str(od_val).strip() != "None":
                try:
                    overdue_days = int(str(od_val).split('.')[0].strip())
                except:
                    pass
            
            # Date types
            due_date = None
            dd_val = get_val("due_date")
            if dd_val is not None and str(dd_val).strip() != "None":
                import datetime as dt_mod
                if isinstance(dd_val, dt_mod.datetime) or isinstance(dd_val, dt_mod.date):
                    due_date = dd_val
                else:
                    try:
                        due_date = datetime.strptime(str(dd_val).strip()[:10], "%Y-%m-%d")
                    except:
                        pass
            
            # Emergency contacts
            v = get_val("emergency_contact_1_name")
            ec1_name = str(v).strip() if v is not None and str(v).strip() != "None" else None
            
            v = get_val("emergency_contact_1_phone")
            ec1_phone = str(v).strip() if v is not None and str(v).strip() != "None" else None
            
            v = get_val("emergency_contact_2_name")
            ec2_name = str(v).strip() if v is not None and str(v).strip() != "None" else None
            
            v = get_val("emergency_contact_2_phone")
            ec2_phone = str(v).strip() if v is not None and str(v).strip() != "None" else None

            # Handle "None" string literal check
            address = address if address and address.lower() != "none" else None
            phone = phone if phone and phone.lower() != "none" else None
            loan_number = loan_number if loan_number and loan_number.lower() != "none" else None
            platform_name = platform_name if platform_name and platform_name.lower() != "none" else None

            # GPS
            lat_val = get_val("lat")
            lat = None
            if lat_val is not None and str(lat_val).strip() != "None":
                try: lat = float(str(lat_val).strip())
                except: pass

            lng_val = get_val("lng")
            lng = None
            if lng_val is not None and str(lng_val).strip() != "None":
                try: lng = float(str(lng_val).strip())
                except: pass

            customer = Customer(
                name=name,
                address=address,
                phone=phone,
                loan_number=loan_number,
                platform_name=platform_name,
                outstanding_amount=outstanding_amount,
                overdue_days=overdue_days,
                due_date=due_date,
                emergency_contact_1_name=ec1_name,
                emergency_contact_1_phone=ec1_phone,
                emergency_contact_2_name=ec2_name,
                emergency_contact_2_phone=ec2_phone,
                lat=lat,
                lng=lng,
                assigned_agent_id=agent_id_val,
                upload_batch=batch_code,
                status="belum",
            )
            db.add(customer)
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

    customers = db.query(Customer).filter(Customer.id.in_(ids)).all()
    deleted_count = 0
    for c in customers:
        db.delete(c)
        deleted_count += 1

    log = ActivityLog(
        user_id=current_user.id,
        action="delete_bulk_customer",
        detail=f"Menghapus secara massal {deleted_count} customers",
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

    customers = db.query(Customer).filter(Customer.upload_batch == batch_code).all()
    count = len(customers)
    for c in customers:
        db.delete(c)

    log = ActivityLog(
        user_id=current_user.id,
        action="delete_batch",
        detail=f"Hapus batch {batch_code} ({count} customers)",
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

    name = customer.name
    db.delete(customer)

    log = ActivityLog(
        user_id=current_user.id,
        action="delete_customer",
        detail=f"Hapus customer: {name}",
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
