import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Issue, Document, User, ExtractedField
from backend.app.core.dependencies import get_current_user
from backend.app.services.ocr.processor import process_document_ocr

logger = logging.getLogger("evidencerag.evidence")

router = APIRouter(prefix="/evidence", tags=["Evidence Highlighting"])

@router.get("/{issue_id}")
def get_issue_evidence(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve exact page reference, bounding box coordinates, and visual context
    for any detected issue to power the Evidence Highlighting Viewer.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found.")

    # Verification / user ownership check
    if issue.verification and issue.verification.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view evidence for this issue."
        )

    doc = None
    if issue.document_id:
        doc = db.query(Document).filter(Document.id == issue.document_id).first()

    # Calculate bounding box
    bbox = None
    is_exact_bbox = False

    if issue.bbox_x is not None and issue.bbox_y is not None:
        bbox = {
            "x": issue.bbox_x,
            "y": issue.bbox_y,
            "width": issue.bbox_width or 0.3,
            "height": issue.bbox_height or 0.05
        }
        is_exact_bbox = True
    elif doc:
        # Search extracted fields or OCR blocks for snippet occurrence
        search_term = (issue.actual_value or issue.evidence_snippet or "").strip().lower()
        if search_term and len(search_term) > 2:
            try:
                ocr_data = process_document_ocr(doc.file_path, doc.mime_type)
                for block in ocr_data.get("blocks", []):
                    if search_term in block.get("text", "").lower():
                        b = block.get("bbox", [0.1, 0.2, 0.5, 0.05])
                        bbox = {
                            "x": b[0],
                            "y": b[1],
                            "width": b[2],
                            "height": b[3]
                        }
                        is_exact_bbox = True
                        break
            except Exception as e:
                logger.warning(f"Could not compute OCR bounding box for issue {issue_id}: {e}")

    # Fallback bounding box if not found: highlight page header/snippet zone
    if not bbox:
        bbox = {
            "x": 0.1,
            "y": 0.25,
            "width": 0.8,
            "height": 0.08
        }
        is_exact_bbox = False

    return {
        "issue_id": issue.id,
        "verification_id": issue.verification_id,
        "title": issue.title,
        "category": issue.category,
        "severity": issue.severity,
        "document_id": doc.id if doc else None,
        "document_name": doc.original_filename if doc else (issue.document_name or "Uploaded Credential"),
        "page_number": issue.page_number or 1,
        "evidence_snippet": issue.evidence_snippet,
        "expected_value": issue.expected_value,
        "actual_value": issue.actual_value,
        "explanation": issue.explanation,
        "suggested_correction": issue.suggested_correction,
        "confidence_score": issue.confidence_score,
        "manual_review_recommended": issue.manual_review_recommended,
        "rag_rule_id": issue.rag_rule_id,
        "rag_source": issue.rag_source,
        "bbox": bbox,
        "is_exact_bbox": is_exact_bbox,
        "preview_url": f"/api/documents/{doc.id}/preview" if doc else None
    }
