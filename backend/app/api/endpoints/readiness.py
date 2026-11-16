import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Document, Issue, VerificationResult, User, ReadinessScore, VerificationRule
from backend.app.core.dependencies import get_current_user

logger = logging.getLogger("evidencerag.readiness")

router = APIRouter(prefix="/readiness", tags=["Readiness Scoring"])

def calculate_document_readiness(doc: Document, db: Session) -> Dict[str, Any]:
    """
    Calculate transparent 0-100 readiness score for an individual document
    based on completeness, confirmed errors, blur/resolution, and unresolved warnings.
    """
    # 1. Base components (each out of 100)
    completeness = 100
    quality = int(round((doc.image_quality_score or 1.0) * 100))
    validation = 100
    deductions: List[Dict[str, Any]] = []

    # Check blur and resolution
    if doc.is_blurry:
        quality = max(20, quality - 30)
        deductions.append({
            "category": "Scan Quality",
            "points": 15,
            "reason": "Image blur detected (Laplacian variance low); OCR text may be compromised."
        })
    if doc.is_low_res:
        quality = max(30, quality - 20)
        deductions.append({
            "category": "Resolution",
            "points": 10,
            "reason": "Scan resolution is below recommended 150-300 DPI benchmark."
        })

    # Check issues associated with this document
    issues = db.query(Issue).filter(Issue.document_id == doc.id).all()
    
    for iss in issues:
        sev = iss.severity.lower()
        if sev == "critical":
            validation = max(0, validation - 35)
            deductions.append({
                "category": "Critical Defect",
                "points": 25,
                "reason": f"{iss.title}: {iss.explanation}"
            })
        elif sev == "high":
            validation = max(0, validation - 20)
            deductions.append({
                "category": "High Risk Defect",
                "points": 15,
                "reason": f"{iss.title}: {iss.explanation}"
            })
        elif sev == "medium":
            validation = max(0, validation - 10)
            deductions.append({
                "category": "Warning",
                "points": 8,
                "reason": f"{iss.title}"
            })
        else:
            validation = max(0, validation - 5)

    # Check mandatory fields against active rule for this category
    rule = db.query(VerificationRule).filter(
        VerificationRule.document_category == doc.category,
        VerificationRule.is_active == True
    ).first()

    if rule and rule.mandatory_fields:
        try:
            m_fields = json.loads(rule.mandatory_fields)
            ext_names = [f.field_name for f in doc.extracted_fields]
            missing = [mf for mf in m_fields if mf not in ext_names]
            for mf in missing:
                completeness = max(0, completeness - 25)
                deductions.append({
                    "category": "Missing Field",
                    "points": 20,
                    "reason": f"Mandatory statutory field '{mf}' was not recognized."
                })
        except Exception:
            pass

    # Total score formula: 40% Completeness + 40% Validation + 20% Visual Quality
    total_score = int(round((0.40 * completeness) + (0.40 * validation) + (0.20 * quality)))
    total_score = max(0, min(100, total_score))

    # Readiness tier
    if total_score >= 90:
        status_label = "Ready for Submission"
        badge_color = "emerald"
    elif total_score >= 70:
        status_label = "Review Recommended"
        badge_color = "amber"
    else:
        status_label = "Correction Required"
        badge_color = "rose"

    return {
        "document_id": doc.id,
        "document_name": doc.original_filename,
        "category": doc.category,
        "overall_score": total_score,
        "readiness_status": status_label,
        "badge_color": badge_color,
        "breakdown": {
            "completeness_score": completeness,
            "validation_score": validation,
            "quality_score": quality
        },
        "deductions": deductions,
        "scoring_formula": "40% Field Completeness + 40% Validation Cleanliness + 20% Scan Quality",
        "actionable_improvements": [
            d["reason"] for d in deductions
        ]
    }

@router.get("")
def get_application_readiness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregate scholarship application readiness score across all documents
    uploaded by the authenticated student.
    """
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    if not docs:
        return {
            "application_score": 0,
            "readiness_status": "No Documents Uploaded",
            "badge_color": "slate",
            "total_documents": 0,
            "verified_count": 0,
            "documents": [],
            "overall_deductions": [],
            "advice": "Upload your required scholarship certificates to calculate your application submission readiness score."
        }

    doc_scores = [calculate_document_readiness(d, db) for d in docs]
    avg_score = int(round(sum(s["overall_score"] for s in doc_scores) / len(doc_scores)))

    all_deductions = []
    for s in doc_scores:
        for d in s["deductions"]:
            all_deductions.append({
                "document": s["document_name"],
                **d
            })

    if avg_score >= 90:
        app_status = "Application Submission Ready"
        color = "emerald"
    elif avg_score >= 70:
        app_status = "Passed with Caution"
        color = "amber"
    else:
        app_status = "Action Required Before Submission"
        color = "rose"

    return {
        "application_score": avg_score,
        "readiness_status": app_status,
        "badge_color": color,
        "total_documents": len(docs),
        "documents": doc_scores,
        "overall_deductions": all_deductions,
        "formula": "Weighted average of verified certificate scores based on statutory completeness and defect absence."
    }

@router.get("/{document_id}")
def get_single_document_readiness(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transparent readiness score for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to view this document.")

    return calculate_document_readiness(doc, db)
