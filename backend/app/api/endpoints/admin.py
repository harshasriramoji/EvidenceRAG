import json
import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Document, VerificationResult, Issue, VerificationRule, AdminReview,
    AuditLog, ReferenceMaterial
)
from backend.app.core.dependencies import get_current_admin
from backend.app.core.config import settings
from backend.app.services.rag.engine import rag_engine

router = APIRouter(prefix="/admin", tags=["Admin"])

class AdminReviewCreate(BaseModel):
    decision: str  # approved, rejected, override_pass, requires_resubmission
    admin_notes: Optional[str] = None

class VerificationRuleCreate(BaseModel):
    rule_code: str
    document_category: str
    name: str
    description: str
    mandatory_fields: List[str]
    validity_period_months: int = 0

class VerificationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    mandatory_fields: Optional[List[str]] = None
    validity_period_months: Optional[int] = None
    is_active: Optional[bool] = None

@router.get("/dashboard")
def get_admin_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_docs = db.query(func.count(Document.id)).scalar() or 0
    total_verifications = db.query(func.count(VerificationResult.id)).scalar() or 0

    # Status counts
    passed_count = db.query(func.count(VerificationResult.id)).filter(
        VerificationResult.overall_status == "Passed"
    ).scalar() or 0
    warning_count = db.query(func.count(VerificationResult.id)).filter(
        VerificationResult.overall_status == "Passed with Warnings"
    ).scalar() or 0
    correction_count = db.query(func.count(VerificationResult.id)).filter(
        VerificationResult.overall_status == "Needs Correction"
    ).scalar() or 0
    manual_review_count = db.query(func.count(VerificationResult.id)).filter(
        VerificationResult.overall_status == "Manual Review Required"
    ).scalar() or 0

    # Flagged issues needing review
    pending_reviews_count = db.query(func.count(Issue.id)).filter(
        Issue.manual_review_recommended == True
    ).scalar() or 0

    # Recent activities
    recent_verifications = db.query(VerificationResult).order_by(
        VerificationResult.created_at.desc()
    ).limit(8).all()

    recent_activity = [
        {
            "id": v.id,
            "user_email": v.user.email if v.user else "Anonymous",
            "mode": v.verification_mode,
            "overall_status": v.overall_status,
            "total_issues": v.total_issues,
            "created_at": v.created_at
        }
        for v in recent_verifications
    ]

    return {
        "total_users": total_users,
        "total_documents": total_docs,
        "total_verifications": total_verifications,
        "passed_documents": passed_count,
        "warning_cases": warning_count,
        "correction_cases": correction_count,
        "manual_review_queue": manual_review_count,
        "pending_issues_review": pending_reviews_count,
        "recent_activity": recent_activity
    }

@router.get("/users")
def get_admin_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    res = []
    for u in users:
        doc_count = db.query(func.count(Document.id)).filter(Document.user_id == u.id).scalar() or 0
        v_count = db.query(func.count(VerificationResult.id)).filter(VerificationResult.user_id == u.id).scalar() or 0
        res.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "document_count": doc_count,
            "verification_count": v_count,
            "created_at": u.created_at
        })
    return res

@router.get("/documents")
def get_admin_documents(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    docs = db.query(Document).order_by(Document.created_at.desc()).limit(100).all()
    res = []
    for d in docs:
        res.append({
            "id": d.id,
            "filename": d.filename,
            "original_filename": d.original_filename,
            "user_email": d.user.email if d.user else "N/A",
            "category": d.category,
            "file_size": d.file_size,
            "quality_score": d.image_quality_score,
            "is_blurry": d.is_blurry,
            "is_low_res": d.is_low_res,
            "upload_status": d.upload_status,
            "created_at": d.created_at
        })
    return res

@router.get("/reviews")
def get_flagged_issues(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    issues = db.query(Issue).filter(
        Issue.manual_review_recommended == True
    ).order_by(Issue.created_at.desc()).all()

    res = []
    for iss in issues:
        existing_review = db.query(AdminReview).filter(AdminReview.issue_id == iss.id).first()
        res.append({
            "id": iss.id,
            "verification_id": iss.verification_id,
            "title": iss.title,
            "category": iss.category,
            "severity": iss.severity,
            "document_name": iss.document_name,
            "evidence_snippet": iss.evidence_snippet,
            "expected_value": iss.expected_value,
            "actual_value": iss.actual_value,
            "explanation": iss.explanation,
            "suggested_correction": iss.suggested_correction,
            "created_at": iss.created_at,
            "admin_review": {
                "id": existing_review.id,
                "decision": existing_review.decision,
                "admin_notes": existing_review.admin_notes,
                "reviewed_at": existing_review.reviewed_at
            } if existing_review else None
        })
    return res

@router.post("/reviews/{issue_id}", status_code=status.HTTP_201_CREATED)
def record_issue_review(
    issue_id: int,
    review_data: AdminReviewCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    iss = db.query(Issue).filter(Issue.id == issue_id).first()
    if not iss:
        raise HTTPException(status_code=404, detail="Issue not found.")

    valid_decisions = ["approved", "rejected", "override_pass", "requires_resubmission"]
    if review_data.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}"
        )

    # Log administrative action in AuditLog
    audit = AuditLog(
        user_id=current_admin.id,
        action="ADMIN_REVIEW_DECISION",
        target_type="issue",
        target_id=iss.id,
        details=f"Decision '{review_data.decision}' recorded for Issue #{iss.id} on document '{iss.document_name}'. Notes: {review_data.admin_notes or 'None'}"
    )
    db.add(audit)

    if existing_review:
        existing_review.decision = review_data.decision
        existing_review.admin_notes = review_data.admin_notes
        existing_review.admin_id = current_admin.id
        existing_review.reviewed_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing_review)
        return {"message": "Admin review updated.", "review_id": existing_review.id}
    else:
        new_rev = AdminReview(
            issue_id=iss.id,
            admin_id=current_admin.id,
            decision=review_data.decision,
            admin_notes=review_data.admin_notes,
            reviewed_at=datetime.datetime.utcnow()
        )
        db.add(new_rev)
        db.commit()
        db.refresh(new_rev)
        return {"message": "Admin review recorded.", "review_id": new_rev.id}

@router.get("/rules")
def get_verification_rules(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    rules = db.query(VerificationRule).order_by(VerificationRule.id.asc()).all()
    res = []
    for r in rules:
        fields = []
        try:
            fields = json.loads(r.mandatory_fields)
        except Exception:
            pass
        res.append({
            "id": r.id,
            "rule_code": r.rule_code,
            "document_category": r.document_category,
            "name": r.name,
            "description": r.description,
            "mandatory_fields": fields,
            "validity_period_months": r.validity_period_months,
            "is_active": r.is_active,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        })
    return res

@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_verification_rule(
    rule_in: VerificationRuleCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(VerificationRule).filter(VerificationRule.rule_code == rule_in.rule_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Rule with code '{rule_in.rule_code}' already exists.")

    new_rule = VerificationRule(
        rule_code=rule_in.rule_code,
        document_category=rule_in.document_category,
        name=rule_in.name,
        description=rule_in.description,
        mandatory_fields=json.dumps(rule_in.mandatory_fields),
        validity_period_months=rule_in.validity_period_months,
        is_active=True
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return {"message": "Rule created successfully.", "rule_id": new_rule.id}

@router.put("/rules/{rule_id}")
def update_verification_rule(
    rule_id: int,
    rule_in: VerificationRuleUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    rule = db.query(VerificationRule).filter(VerificationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")

    if rule_in.name is not None:
        rule.name = rule_in.name
    if rule_in.description is not None:
        rule.description = rule_in.description
    if rule_in.mandatory_fields is not None:
        rule.mandatory_fields = json.dumps(rule_in.mandatory_fields)
    if rule_in.validity_period_months is not None:
        rule.validity_period_months = rule_in.validity_period_months
    if rule_in.is_active is not None:
        rule.is_active = rule_in.is_active

    # Record administrative action in AuditLog
    audit = AuditLog(
        user_id=current_admin.id,
        action="UPDATE_VERIFICATION_RULE",
        target_type="verification_rule",
        target_id=rule.id,
        details=f"Updated rule '{rule.rule_code}' ({rule.name})"
    )
    db.add(audit)

    db.commit()
    db.refresh(rule)
    return {"message": "Rule updated successfully.", "rule_id": rule.id}

@router.get("/metrics")
def get_ml_metrics(
    current_admin: User = Depends(get_current_admin)
):
    metrics_path = settings.MODELS_DIR / "evaluation_metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="ML evaluation metrics not found.")
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    return metrics

# -------------------------------------------------------------
# Knowledge Base Management & Semantic RAG Testing Endpoints
# -------------------------------------------------------------
class KnowledgeRuleCreate(BaseModel):
    id: str
    category: str
    title: str
    content: str
    source: str
    mandatory_fields: List[str] = []
    validity_months: int = 0

class KnowledgeRuleUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    mandatory_fields: Optional[List[str]] = None
    validity_months: Optional[int] = None

class TestQueryRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top_k: int = 3

@router.get("/knowledge-base")
def get_knowledge_base_rules(
    current_admin: User = Depends(get_current_admin)
):
    """Return all regulatory verification rules in the active RAG knowledge base."""
    return {
        "total_rules": len(rag_engine.rules),
        "rules": rag_engine.rules,
        "embedding_model": settings.EMBEDDING_MODEL,
        "ollama_model": settings.OLLAMA_MODEL
    }

@router.post("/knowledge-base/test-query")
def test_rag_retrieval(
    test_req: TestQueryRequest,
    current_admin: User = Depends(get_current_admin)
):
    """
    Simulate semantic retrieval and RAG explanation generation for any arbitrary query/finding.
    Allows administrators to test and fine-tune RAG performance live.
    """
    if not test_req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    # Retrieve relevant rules
    retrieved = rag_engine.retrieve(
        query=test_req.query,
        category=test_req.category,
        top_k=test_req.top_k
    )

    # Generate explanation preview
    explanation_res = rag_engine.generate_explanation(
        issue_title=test_req.query,
        category=test_req.category or "General",
        evidence=f"Sample test query: '{test_req.query}'",
        expected_val="Compliant with portal statutory norms",
        actual_val=test_req.query
    )

    return {
        "query": test_req.query,
        "category_filter": test_req.category,
        "top_k": test_req.top_k,
        "retrieved_count": len(retrieved),
        "retrieved_rules": retrieved,
        "rag_preview": explanation_res
    }

@router.post("/knowledge-base", status_code=status.HTTP_201_CREATED)
def add_knowledge_rule(
    rule_in: KnowledgeRuleCreate,
    current_admin: User = Depends(get_current_admin)
):
    """Add a new regulatory rule to the RAG knowledge base."""
    existing = [r for r in rag_engine.rules if r["id"] == rule_in.id]
    if existing:
        raise HTTPException(status_code=400, detail=f"Knowledge rule with ID '{rule_in.id}' already exists.")

    new_rule = rule_in.dict()
    rag_engine.add_rule(new_rule)
    return {"message": "Knowledge rule added successfully.", "rule": new_rule}

@router.put("/knowledge-base/{rule_id}")
def update_knowledge_rule(
    rule_id: str,
    rule_in: KnowledgeRuleUpdate,
    current_admin: User = Depends(get_current_admin)
):
    """Update an existing regulatory rule in the RAG knowledge base."""
    updated = rag_engine.update_rule(rule_id, rule_in.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Knowledge rule '{rule_id}' not found.")
    return {"message": "Knowledge rule updated successfully.", "rule": updated}

@router.delete("/knowledge-base/{rule_id}")
def delete_knowledge_rule(
    rule_id: str,
    current_admin: User = Depends(get_current_admin)
):
    """Remove a regulatory rule from the RAG knowledge base."""
    deleted = rag_engine.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Knowledge rule '{rule_id}' not found.")
    return {"message": f"Knowledge rule '{rule_id}' removed successfully."}

# -------------------------------------------------------------
# Admin Audit Trail & Reference Materials Endpoints
# -------------------------------------------------------------
class ReferenceMaterialCreate(BaseModel):
    title: str
    category: str
    content: str
    source: str
    authority: Optional[str] = "Government Authority"

@router.get("/audit-logs")
def get_admin_audit_logs(
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve chronological administrative audit trail recording issue reviews,
    rule revisions, document uploads, and decision overrides.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    res = []
    for l in logs:
        user_email = l.user.email if l.user else "System"
        res.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_email": user_email,
            "action": l.action,
            "target_type": l.target_type,
            "target_id": l.target_id,
            "details": l.details,
            "ip_address": l.ip_address,
            "timestamp": l.timestamp
        })
    return res

@router.get("/reference-materials")
def list_reference_materials(
    category: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List administrative reference materials and official statutory documentation."""
    query = db.query(ReferenceMaterial)
    if category:
        query = query.filter(ReferenceMaterial.category == category)
    materials = query.order_by(ReferenceMaterial.id.asc()).all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "category": m.category,
            "content": m.content,
            "source": m.source,
            "authority": m.authority,
            "created_at": m.created_at
        }
        for m in materials
    ]

@router.post("/reference-materials", status_code=status.HTTP_201_CREATED)
def create_reference_material(
    mat_in: ReferenceMaterialCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Add a new official reference material / statutory guideline to the system repository."""
    mat = ReferenceMaterial(
        title=mat_in.title,
        category=mat_in.category,
        content=mat_in.content,
        source=mat_in.source,
        authority=mat_in.authority or "Government Authority",
        is_active=True
    )
    db.add(mat)
    db.commit()
    db.refresh(mat)

    # Log audit entry
    audit = AuditLog(
        user_id=current_admin.id,
        action="ADD_REFERENCE_MATERIAL",
        target_type="reference_material",
        target_id=mat.id,
        details=f"Added reference material: '{mat.title}' ({mat.category})"
    )
    db.add(audit)
    db.commit()

    return {"message": "Reference material created successfully.", "id": mat.id}

