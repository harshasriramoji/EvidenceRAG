import uuid
import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Application, Document, User, Notification, AuditLog
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/applications", tags=["Applicant Workspace - Applications"])

class ApplicationCreate(BaseModel):
    title: str
    scholarship_name: str
    academic_year: Optional[str] = "2025-2026"
    notes: Optional[str] = None

class ApplicationUpdate(BaseModel):
    title: Optional[str] = None
    scholarship_name: Optional[str] = None
    academic_year: Optional[str] = None
    notes: Optional[str] = None

@router.post("", status_code=status.HTTP_201_CREATED)
def create_application(
    app_in: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scholarship application portfolio."""
    app_num = f"APP-{datetime.datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    new_app = Application(
        user_id=current_user.id,
        application_number=app_num,
        title=app_in.title,
        scholarship_name=app_in.scholarship_name,
        academic_year=app_in.academic_year or "2025-2026",
        notes=app_in.notes,
        status="Draft"
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    # Log audit entry
    audit = AuditLog(
        user_id=current_user.id,
        action="CREATE_APPLICATION",
        target_type="application",
        target_id=new_app.id,
        details=f"Created application {app_num}: {new_app.title} ({new_app.scholarship_name})"
    )
    db.add(audit)

    # User notification
    notif = Notification(
        user_id=current_user.id,
        title="Application Portfolio Created",
        message=f"Application '{new_app.title}' ({app_num}) has been created in Draft status. You can now attach verified documents.",
        category="success",
        link=f"/applications/{new_app.id}"
    )
    db.add(notif)
    db.commit()

    return {
        "id": new_app.id,
        "application_number": new_app.application_number,
        "title": new_app.title,
        "scholarship_name": new_app.scholarship_name,
        "status": new_app.status,
        "academic_year": new_app.academic_year,
        "created_at": new_app.created_at
    }

@router.get("")
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List applications for the current user (or all if reviewer/admin)."""
    if current_user.role in ("admin", "reviewer"):
        apps = db.query(Application).order_by(Application.created_at.desc()).all()
    else:
        apps = db.query(Application).filter(Application.user_id == current_user.id).order_by(Application.created_at.desc()).all()

    return [
        {
            "id": a.id,
            "application_number": a.application_number,
            "title": a.title,
            "scholarship_name": a.scholarship_name,
            "status": a.status,
            "academic_year": a.academic_year,
            "applicant_email": a.user.email if a.user else "N/A",
            "document_count": len(a.documents),
            "submitted_at": a.submitted_at,
            "created_at": a.created_at,
            "updated_at": a.updated_at
        }
        for a in apps
    ]

@router.get("/{application_id}")
def get_application_detail(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full application details, status timeline, and attached documents."""
    app_obj = db.query(Application).filter(Application.id == application_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    if app_obj.user_id != current_user.id and current_user.role not in ("admin", "reviewer"):
        raise HTTPException(status_code=403, detail="Access denied to this application.")

    docs = [
        {
            "id": d.id,
            "filename": d.original_filename,
            "category": d.category,
            "quality_score": d.image_quality_score,
            "version": d.version,
            "created_at": d.created_at
        }
        for d in app_obj.documents
    ]

    return {
        "id": app_obj.id,
        "application_number": app_obj.application_number,
        "title": app_obj.title,
        "scholarship_name": app_obj.scholarship_name,
        "status": app_obj.status,
        "academic_year": app_obj.academic_year,
        "notes": app_obj.notes,
        "reviewer_notes": app_obj.reviewer_notes,
        "applicant_id": app_obj.user_id,
        "applicant_email": app_obj.user.email if app_obj.user else "N/A",
        "submitted_at": app_obj.submitted_at,
        "created_at": app_obj.created_at,
        "documents": docs,
        "timeline": [
            {"status": "Draft", "timestamp": app_obj.created_at, "completed": True},
            {"status": "Submitted", "timestamp": app_obj.submitted_at, "completed": app_obj.status != "Draft"},
            {"status": "Under Review", "timestamp": None, "completed": app_obj.status in ("Under Review", "Verified", "Flagged")},
            {"status": "Final Assessment", "timestamp": None, "completed": app_obj.status in ("Verified", "Flagged")}
        ]
    }

@router.post("/{application_id}/submit")
def submit_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit application for official human reviewer verification."""
    app_obj = db.query(Application).filter(Application.id == application_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    if app_obj.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot submit another user's application.")

    if not app_obj.documents:
        raise HTTPException(status_code=400, detail="Cannot submit an application without any attached documents.")

    app_obj.status = "Submitted"
    app_obj.submitted_at = datetime.datetime.utcnow()
    db.commit()

    # Log audit entry
    audit = AuditLog(
        user_id=current_user.id,
        action="SUBMIT_APPLICATION",
        target_type="application",
        target_id=app_obj.id,
        details=f"Submitted application {app_obj.application_number} with {len(app_obj.documents)} attached certificates."
    )
    db.add(audit)

    # Notification
    notif = Notification(
        user_id=current_user.id,
        title="Application Submitted",
        message=f"Application {app_obj.application_number} has been submitted for official review.",
        category="info",
        link=f"/applications/{app_obj.id}"
    )
    db.add(notif)
    db.commit()

    return {"message": "Application submitted successfully.", "status": app_obj.status}

@router.post("/{application_id}/attach-document/{document_id}")
def attach_document_to_application(
    application_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attach an uploaded certificate document to this application."""
    app_obj = db.query(Application).filter(Application.id == application_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    if app_obj.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot modify this application.")

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot attach another user's document.")

    doc.application_id = app_obj.id
    db.commit()

    return {"message": f"Document '{doc.original_filename}' attached to application {app_obj.application_number}."}
