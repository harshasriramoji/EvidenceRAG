import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Document, Issue, VerificationResult, ScholarshipRequirement
)
from backend.app.core.dependencies import get_current_user, get_current_admin

logger = logging.getLogger("evidencerag.checklist")

router = APIRouter(prefix="/checklist", tags=["Scholarship Application Readiness Checklist"])

class ScholarshipRequirementCreate(BaseModel):
    scholarship_name: str
    description: Optional[str] = None
    required_categories: List[str]
    min_readiness_score: int = 80

class ScholarshipRequirementUpdate(BaseModel):
    scholarship_name: Optional[str] = None
    description: Optional[str] = None
    required_categories: Optional[List[str]] = None
    min_readiness_score: Optional[int] = None
    is_active: Optional[bool] = None

@router.get("")
def get_user_checklist(
    scheme_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluate student's uploaded documents against the selected scholarship scheme checklist
    and compute completion progress percentage, missing requirements, and status.
    """
    # 1. Fetch available scholarship schemes
    schemes = db.query(ScholarshipRequirement).filter(ScholarshipRequirement.is_active == True).all()
    if not schemes:
        return {"schemes": [], "checklist": None}

    # Select target scheme
    selected_scheme = None
    if scheme_id:
        selected_scheme = db.query(ScholarshipRequirement).filter(ScholarshipRequirement.id == scheme_id).first()
    if not selected_scheme:
        selected_scheme = schemes[0]

    # Parse required categories
    try:
        req_cats = json.loads(selected_scheme.required_categories)
    except Exception:
        req_cats = ["Aadhaar Card", "Income Certificate", "Caste Certificate", "Bank Passbook"]

    # 2. Fetch authenticated student's documents and verified issues
    user_docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    uploaded_cats = {d.category: d for d in user_docs}

    checklist_items = []
    satisfied_count = 0

    for cat in req_cats:
        doc = uploaded_cats.get(cat)
        if doc:
            issues = db.query(Issue).filter(Issue.document_id == doc.id).all()
            critical_issues = [i for i in issues if i.severity.lower() == "critical"]
            has_manual_review = any(i.manual_review_recommended for i in issues)

            if critical_issues:
                item_status = "Needs Correction"
                color = "rose"
            elif has_manual_review:
                item_status = "Awaiting Review"
                color = "purple"
            elif issues:
                item_status = "Passed with Warnings"
                color = "amber"
                satisfied_count += 1
            else:
                item_status = "Verified & Complete"
                color = "emerald"
                satisfied_count += 1

            checklist_items.append({
                "category": cat,
                "is_uploaded": True,
                "document_id": doc.id,
                "document_name": doc.original_filename,
                "status": item_status,
                "color": color,
                "issue_count": len(issues),
                "action_needed": critical_issues[0].suggested_correction if critical_issues else None
            })
        else:
            checklist_items.append({
                "category": cat,
                "is_uploaded": False,
                "document_id": None,
                "document_name": None,
                "status": "Missing Document",
                "color": "slate",
                "issue_count": 0,
                "action_needed": f"Upload genuine {cat} scan to fulfill application checklist."
            })

    progress_percentage = int(round((satisfied_count / len(req_cats)) * 100)) if req_cats else 0

    formatted_schemes = [
        {
            "id": s.id,
            "name": s.scholarship_name,
            "description": s.description,
            "min_score": s.min_readiness_score
        }
        for s in schemes
    ]

    return {
        "selected_scheme": {
            "id": selected_scheme.id,
            "name": selected_scheme.scholarship_name,
            "description": selected_scheme.description,
            "min_score": selected_scheme.min_readiness_score
        },
        "available_schemes": formatted_schemes,
        "progress_percentage": progress_percentage,
        "total_required": len(req_cats),
        "satisfied_count": satisfied_count,
        "missing_count": len(req_cats) - len([c for c in checklist_items if c["is_uploaded"]]),
        "checklist": checklist_items
    }

@router.post("/requirements", status_code=status.HTTP_201_CREATED)
def create_scholarship_requirement(
    req_in: ScholarshipRequirementCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to create a new scholarship requirement scheme."""
    new_scheme = ScholarshipRequirement(
        scholarship_name=req_in.scholarship_name,
        description=req_in.description,
        required_categories=json.dumps(req_in.required_categories),
        min_readiness_score=req_in.min_readiness_score,
        is_active=True
    )
    db.add(new_scheme)
    db.commit()
    db.refresh(new_scheme)
    return {"message": "Scholarship requirement scheme created.", "scheme_id": new_scheme.id}

@router.put("/requirements/{scheme_id}")
def update_scholarship_requirement(
    scheme_id: int,
    req_in: ScholarshipRequirementUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to update an existing scholarship scheme requirement."""
    scheme = db.query(ScholarshipRequirement).filter(ScholarshipRequirement.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scholarship requirement scheme not found.")

    if req_in.scholarship_name is not None:
        scheme.scholarship_name = req_in.scholarship_name
    if req_in.description is not None:
        scheme.description = req_in.description
    if req_in.required_categories is not None:
        scheme.required_categories = json.dumps(req_in.required_categories)
    if req_in.min_readiness_score is not None:
        scheme.min_readiness_score = req_in.min_readiness_score
    if req_in.is_active is not None:
        scheme.is_active = req_in.is_active

    db.commit()
    db.refresh(scheme)
    return {"message": "Scholarship requirement scheme updated.", "scheme_id": scheme.id}
