import os
import uuid
import shutil
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Document, ExtractedField, User, DocumentVersion, AuditLog
from backend.app.schemas.document import DocumentUploadResponse, DocumentListItem, DocumentDetail, ExtractedFieldSchema
from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.services.ocr.processor import process_document_ocr
from backend.app.services.ocr.extractor import FieldExtractor

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".doc"}
ALLOWED_MIME_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/jpg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword", "application/octet-stream"
}
VALID_CATEGORIES = [
    "Aadhaar Card",
    "Income Certificate",
    "Caste Certificate",
    "Residence Certificate",
    "Study Certificate",
    "Bonafide Certificate",
    "Marks Memo",
    "Bank Passbook",
    "Passport-size Photograph",
    "Other Supporting Documents"
]

@router.post("/upload", response_model=List[DocumentUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )

    if not files or len(files) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")

    uploaded_docs = []

    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, JPG, JPEG, PNG."
            )

        # Check content length / read bytes safely
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' is empty (0 bytes)."
            )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # Check duplicate upload for current user
        existing_doc = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.original_filename == file.filename,
            Document.file_size == len(content)
        ).first()
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate document detected: '{file.filename}' has already been uploaded."
            )

        # MIME type validation if provided
        if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES and file.content_type != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported MIME type '{file.content_type}'. Allowed types: PDF, JPEG, PNG."
            )

        # Generate unique safe filename
        safe_uid = uuid.uuid4().hex
        stored_filename = f"{safe_uid}{ext}"
        stored_path = settings.UPLOAD_DIR / stored_filename

        # Write to disk
        with open(stored_path, "wb") as f_out:
            f_out.write(content)

        mime_type = file.content_type or ("application/pdf" if ext == ".pdf" else "image/jpeg")

        # Process OCR & Quality
        try:
            ocr_result = process_document_ocr(str(stored_path), mime_type)
        except Exception as e:
            if stored_path.exists():
                stored_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Corrupted or unreadable document '{file.filename}': {str(e)}"
            )

        # Create Document record
        doc_record = Document(
            user_id=current_user.id,
            filename=stored_filename,
            original_filename=file.filename or stored_filename,
            file_path=str(stored_path),
            file_size=len(content),
            mime_type=mime_type,
            category=category,
            upload_status="processed",
            image_quality_score=ocr_result.get("quality_score", 1.0),
            is_blurry=ocr_result.get("is_blurry", False),
            is_low_res=ocr_result.get("is_low_res", False),
            is_rotated=ocr_result.get("is_rotated", False),
            page_count=ocr_result.get("page_count", 1),
            raw_text=ocr_result.get("full_text", "")
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        # Extract Fields
        extracted_fields_data = FieldExtractor.extract_all_fields(
            raw_text=doc_record.raw_text or "",
            category=category,
            page_number=1
        )

        extracted_field_models = []
        for f_data in extracted_fields_data:
            ef = ExtractedField(
                document_id=doc_record.id,
                field_name=f_data["field_name"],
                field_value=f_data["field_value"],
                confidence=f_data["confidence"],
                page_number=f_data["page_number"],
                extraction_method=f_data["extraction_method"]
            )
            db.add(ef)
            extracted_field_models.append(ef)

        db.commit()
        db.refresh(doc_record)

        uploaded_docs.append(DocumentUploadResponse(
            id=doc_record.id,
            filename=doc_record.filename,
            original_filename=doc_record.original_filename,
            category=doc_record.category,
            file_size=doc_record.file_size,
            mime_type=doc_record.mime_type,
            upload_status=doc_record.upload_status,
            page_count=doc_record.page_count,
            quality_score=doc_record.image_quality_score,
            is_blurry=doc_record.is_blurry,
            is_low_res=doc_record.is_low_res,
            is_rotated=doc_record.is_rotated,
            created_at=doc_record.created_at,
            extracted_fields=[ExtractedFieldSchema.from_orm(ef) for ef in extracted_field_models]
        ))

    return uploaded_docs

@router.get("", response_model=List[DocumentListItem])
def list_documents(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if category:
        query = query.filter(Document.category == category)
    docs = query.order_by(Document.created_at.desc()).all()
    return docs

@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    
    # User isolation check (admin can view any document)
    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this document."
        )

    return doc

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document."
        )

    # Delete physical file
    try:
        p = Path(doc.file_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully.", "document_id": document_id}

@router.get("/{document_id}/preview")
def preview_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this document."
        )

    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server.")

    return FileResponse(
        path=str(path),
        media_type=doc.mime_type,
        filename=doc.original_filename
    )

@router.get("/{document_id}/versions")
def get_document_versions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full version history and changes for an uploaded document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to view versions for this document.")

    versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).order_by(DocumentVersion.version_number.desc()).all()

    res = [
        {
            "id": v.id,
            "version_number": v.version_number,
            "file_size": v.file_size,
            "quality_score": v.quality_score,
            "change_summary": v.change_summary or "Historical revision",
            "created_at": v.created_at,
            "is_current": False
        }
        for v in versions
    ]
    # Current active version at head
    res.insert(0, {
        "id": 0,
        "version_number": doc.version,
        "file_size": doc.file_size,
        "quality_score": doc.quality_score,
        "change_summary": "Current active version in repository",
        "created_at": doc.created_at,
        "is_current": True
    })

    return {
        "document_id": doc.id,
        "document_name": doc.original_filename,
        "category": doc.category,
        "current_version": doc.version,
        "total_versions": len(res),
        "versions": res
    }

@router.post("/{document_id}/versions", status_code=status.HTTP_201_CREATED)
async def upload_new_document_version(
    document_id: int,
    file: UploadFile = File(...),
    change_summary: Optional[str] = Form("Uploaded corrected scan / re-submission"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a corrected version of an existing document:
    - Archives current state to DocumentVersion table
    - Increments document version number
    - Re-runs OCR extraction and quality analysis
    - Logs audit trail entry
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to modify this document.")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{ext}'. Allowed: PDF, JPG, PNG.")

    # 1. Archive current active version
    old_fields_dict = {ef.field_name: ef.field_value for ef in doc.extracted_fields}
    archive_version = DocumentVersion(
        document_id=doc.id,
        version_number=doc.version,
        file_path=doc.file_path,
        file_size=doc.file_size,
        raw_text=doc.raw_text,
        quality_score=doc.image_quality_score or 1.0,
        change_summary=change_summary,
        extracted_fields_json=json.dumps(old_fields_dict)
    )
    db.add(archive_version)

    # 2. Save new file
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    new_path = settings.UPLOAD_DIR / safe_name
    content = await file.read()
    with open(new_path, "wb") as f:
        f.write(content)

    # 3. Process OCR on new version
    ocr_res = process_document_ocr(str(new_path), file.content_type or "application/octet-stream")

    # 4. Update Document attributes
    doc.version += 1
    doc.filename = safe_name
    doc.original_filename = file.filename or doc.original_filename
    doc.file_path = str(new_path)
    doc.file_size = len(content)
    doc.raw_text = ocr_res.get("full_text", "")
    doc.image_quality_score = ocr_res.get("quality_score", 1.0)
    doc.is_blurry = ocr_res.get("is_blurry", False)
    doc.is_low_res = ocr_res.get("is_low_res", False)
    doc.is_rotated = ocr_res.get("is_rotated", False)

    # 5. Re-extract structured fields
    db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).delete()
    extracted_fields_data = FieldExtractor.extract_all_fields(
        raw_text=doc.raw_text or "",
        category=doc.category,
        page_number=1
    )
    for f_data in extracted_fields_data:
        db.add(ExtractedField(
            document_id=doc.id,
            field_name=f_data["field_name"],
            field_value=f_data["field_value"],
            confidence=f_data["confidence"],
            page_number=f_data["page_number"],
            extraction_method=f_data["extraction_method"]
        ))

    # 6. Audit log entry
    audit = AuditLog(
        user_id=current_user.id,
        action="UPLOAD_NEW_VERSION",
        target_type="document",
        target_id=doc.id,
        details=f"Uploaded version {doc.version} for '{doc.original_filename}'"
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)

    return {
        "message": f"Successfully updated '{doc.original_filename}' to version {doc.version}.",
        "document_id": doc.id,
        "new_version": doc.version,
        "previous_version": archive_version.version_number,
        "quality_score": doc.quality_score
    }

