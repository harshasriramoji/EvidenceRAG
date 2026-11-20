import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Guideline, User, AuditLog
from backend.app.core.dependencies import get_current_user, get_current_admin
from backend.app.services.ocr.processor import process_document_ocr
from backend.app.core.config import settings

router = APIRouter(prefix="/guidelines", tags=["Guideline Management"])

class GuidelineStatusUpdate(BaseModel):
    is_approved: Optional[bool] = None
    is_active: Optional[bool] = None

@router.get("")
def list_guidelines(
    category: Optional[str] = Query(None),
    authority: Optional[str] = Query(None),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List official scholarship guidelines.
    Only approved and active guidelines are returned for standard verifications.
    """
    query = db.query(Guideline)
    if active_only:
        query = query.filter(Guideline.is_active == True, Guideline.is_approved == True)
    if category:
        query = query.filter(Guideline.category.ilike(f"%{category}%"))
    if authority:
        query = query.filter(Guideline.issuing_authority.ilike(f"%{authority}%"))
    if search:
        query = query.filter(
            (Guideline.title.ilike(f"%{search}%")) |
            (Guideline.content.ilike(f"%{search}%")) |
            (Guideline.guideline_code.ilike(f"%{search}%"))
        )

    guidelines = query.order_by(Guideline.created_at.desc()).all()
    return [
        {
            "id": g.id,
            "guideline_code": g.guideline_code,
            "title": g.title,
            "issuing_authority": g.issuing_authority,
            "category": g.category,
            "source_url": g.source_url,
            "version": g.version,
            "effective_from": g.effective_from,
            "effective_to": g.effective_to,
            "content_preview": g.content[:250] + "..." if len(g.content) > 250 else g.content,
            "is_approved": g.is_approved,
            "is_active": g.is_active,
            "created_at": g.created_at
        }
        for g in guidelines
    ]

@router.get("/{guideline_id}")
def get_guideline_detail(
    guideline_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve full official guideline content, issuing authority, and validity dates."""
    g = db.query(Guideline).filter(Guideline.id == guideline_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Guideline not found.")
    return g

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_guideline(
    title: str = Form(...),
    issuing_authority: str = Form("Government Authority"),
    category: str = Form(...),
    version: str = Form("1.0"),
    effective_from: Optional[str] = Form("2025-04-01"),
    effective_to: Optional[str] = Form("2027-03-31"),
    source_url: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Administrator uploads an official regulatory guideline document (PDF, DOCX, or direct text).
    Extracts policy text and registers guideline with issuing authority and effective dates.
    """
    extracted_content = content or ""
    saved_path = None

    if file:
        safe_name = f"GUIDELINE_{uuid.uuid4().hex[:8]}_{file.filename}"
        dest = settings.UPLOAD_DIR / safe_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = await file.read()
        with open(dest, "wb") as f:
            f.write(body)
        saved_path = str(dest)

        # Extract text via OCR/DOCX processor
        try:
            ocr_res = process_document_ocr(str(dest), file.content_type or "application/pdf")
            if ocr_res.get("full_text"):
                extracted_content = ocr_res["full_text"]
        except Exception as e:
            if not extracted_content:
                extracted_content = f"Official Guideline document: {file.filename}"

    if not extracted_content.strip():
        raise HTTPException(status_code=400, detail="Guideline content cannot be empty. Please upload a file or enter text.")

    code = f"GL-{datetime.datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
    new_gl = Guideline(
        guideline_code=code,
        title=title,
        issuing_authority=issuing_authority,
        category=category,
        source_url=source_url,
        version=version,
        effective_from=effective_from,
        effective_to=effective_to,
        content=extracted_content,
        file_path=saved_path,
        is_approved=True,
        is_active=True
    )
    db.add(new_gl)
    db.commit()
    db.refresh(new_gl)

    # Log audit trail
    audit = AuditLog(
        user_id=current_admin.id,
        action="CREATE_GUIDELINE",
        target_type="guideline",
        target_id=new_gl.id,
        details=f"Admin uploaded guideline '{title}' ({code}) by authority '{issuing_authority}'"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Guideline registered and approved successfully.",
        "id": new_gl.id,
        "guideline_code": new_gl.guideline_code,
        "title": new_gl.title,
        "version": new_gl.version
    }

@router.put("/{guideline_id}/status")
def update_guideline_status(
    guideline_id: int,
    status_in: GuidelineStatusUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin activates, deactivates, approves, or rejects a guideline."""
    g = db.query(Guideline).filter(Guideline.id == guideline_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Guideline not found.")

    if status_in.is_approved is not None:
        g.is_approved = status_in.is_approved
    if status_in.is_active is not None:
        g.is_active = status_in.is_active

    db.commit()
    db.refresh(g)

    # Log audit entry
    audit = AuditLog(
        user_id=current_admin.id,
        action="UPDATE_GUIDELINE_STATUS",
        target_type="guideline",
        target_id=g.id,
        details=f"Updated guideline {g.guideline_code}: is_approved={g.is_approved}, is_active={g.is_active}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Guideline status updated successfully.",
        "id": g.id,
        "is_approved": g.is_approved,
        "is_active": g.is_active
    }
