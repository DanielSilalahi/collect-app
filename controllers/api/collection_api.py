import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.config import settings
from core.dependencies import get_current_user_api
from models.user import User
from models.customer import Customer
from models.collection import Collection
from models.activity_log import ActivityLog
from schemas.collection import CollectionCreateRequest, CollectionSyncRequest, CollectionResponse
from typing import Optional

router = APIRouter(prefix="/api/collections", tags=["Collection API"])


@router.post("", response_model=CollectionResponse)
def create_collection(
    payload: CollectionCreateRequest,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Submit a collection update (status change)."""
    customer = db.query(Customer).filter(
        Customer.id == payload.customer_id,
        Customer.assigned_agent_id == user.id,
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")

    # Validate status
    valid_statuses = ["bayar", "janji_bayar", "tidak_ketemu"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status harus salah satu: {', '.join(valid_statuses)}")

    collection = Collection(
        customer_id=payload.customer_id,
        agent_id=user.id,
        status=payload.status,
        notes=payload.notes,
        gps_lat=payload.gps_lat,
        gps_lng=payload.gps_lng,
        timestamp=payload.timestamp,
    )
    db.add(collection)

    # Update customer status
    customer.status = payload.status
    if payload.notes:
        customer.notes = payload.notes

    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action="collection_update",
        detail=f"Customer #{customer.id} ({customer.name}): {payload.status}",
    )
    db.add(log)
    db.commit()
    db.refresh(collection)

    return CollectionResponse.model_validate(collection)


@router.post("/upload-photo", response_model=CollectionResponse)
async def upload_photo(
    collection_id: int = Form(...),
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Upload photo evidence for a collection."""
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.agent_id == user.id,
    ).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection record tidak ditemukan")

    # Save file
    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    contents = await file.read()

    # Get active coordinates
    lat = gps_lat if gps_lat is not None else collection.gps_lat
    lng = gps_lng if gps_lng is not None else collection.gps_lng

    # Process photo to add watermark
    try:
        import io
        from PIL import Image, ImageDraw, ImageFont, ImageOps
        from datetime import timedelta

        img = Image.open(io.BytesIO(contents))
        img = ImageOps.exif_transpose(img)  # Fix rotation if needed

        draw = ImageDraw.Draw(img, "RGBA")
        width, height = img.size

        # Time logic based on longitude
        offset = 7
        tz_name = "WIB"
        if lng is not None:
            if lng >= 126.0:
                offset = 9
                tz_name = "WIT"
            elif lng >= 116.0:
                offset = 8
                tz_name = "WITA"

        local_time = datetime.utcnow() + timedelta(hours=offset)
        time_str = local_time.strftime("%d %b %Y %H:%M:%S") + f" {tz_name}"

        text_str = f"Date: {time_str}\nLat: {lat or 'N/A'} , Lng: {lng or 'N/A'}"
        
        # Dynamic font size (approx 3% of width)
        font_size = max(20, int(width * 0.03))
        try:
            # On Windows, arial.ttf is typically available
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Calculate bounding box
        margin = max(10, int(width * 0.02))
        bbox = draw.textbbox((0, 0), text_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        rect_h = text_h + margin * 2
        rect_y = height - rect_h

        # Draw semi-transparent rectangle
        draw.rectangle((0, rect_y, width, height), fill=(0, 0, 0, 160))
        
        # Draw text
        draw.text((margin, rect_y + margin), text_str, font=font, fill=(255, 255, 255, 255))
        
        # Save image
        img.convert("RGB").save(filepath, quality=85)
    except Exception as e:
        # Fallback if image processing fails (e.g., unsupported format)
        print(f"[Upload Error] Watermarking failed: {e}")
        with open(filepath, "wb") as f:
            f.write(contents)

    collection.photo_url = f"/uploads/{filename}"
    if gps_lat is not None:
        collection.gps_lat = gps_lat
    if gps_lng is not None:
        collection.gps_lng = gps_lng

    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action="upload_foto",
        detail=f"Collection #{collection_id}, file: {filename}",
    )
    db.add(log)
    db.commit()
    db.refresh(collection)

    return CollectionResponse.model_validate(collection)


@router.post("/sync")
def sync_collections(
    payload: CollectionSyncRequest,
    user: User = Depends(get_current_user_api),
    db: Session = Depends(get_db),
):
    """Batch sync collections from offline queue."""
    synced = []
    errors = []
    now = datetime.utcnow()

    for item in payload.items:
        try:
            customer = db.query(Customer).filter(
                Customer.id == item.customer_id,
                Customer.assigned_agent_id == user.id,
            ).first()
            if not customer:
                errors.append({"customer_id": item.customer_id, "error": "Customer tidak ditemukan"})
                continue

            collection = Collection(
                customer_id=item.customer_id,
                agent_id=user.id,
                status=item.status,
                notes=item.notes,
                gps_lat=item.gps_lat,
                gps_lng=item.gps_lng,
                timestamp=item.timestamp,
                synced_at=now,
            )
            db.add(collection)

            # Update customer status to latest
            customer.status = item.status

            synced.append(item.customer_id)
        except Exception as e:
            errors.append({"customer_id": item.customer_id, "error": str(e)})

    if synced:
        log = ActivityLog(
            user_id=user.id,
            action="batch_sync",
            detail=f"Synced {len(synced)} collections",
        )
        db.add(log)
        db.commit()

    return {
        "synced_count": len(synced),
        "error_count": len(errors),
        "synced": synced,
        "errors": errors,
    }
