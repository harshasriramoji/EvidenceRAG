import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Issue, AdminReview, User, AuditLog, Notification, Application, Document
from backend.app.core.dependencies import get_current_reviewer

router = APIRouter(prefix="/reviews", tags=["Human-in-the-Loop Review Management"])

class ReviewDecisionRequest(BaseModel):
    decision: str  # approved, rejected, override_pass, request_info
    reviewer_comments: Optional[str] = None

@router.get("/queue")
def get_reviewer_queue(
    current_reviewer: User = Depends(get_current_reviewer),
    db: Session = Depends(get_db)
):
    """
    Retrieve queue of flagged issues and submitted applications
    requiring human reviewer evaluation and evidence inspection.
    """
    # 1. Flagged AI issues recommended for manual review
    flagged_issues = db.query(Issue).filter(
        Issue.manual_review_recommended == True
    ).order_by(Issue.created_at.desc()).limit(100).all()

    issue_items = []
    for iss in flagged_issues:
        rev = db.query(AdminReview).filter(AdminReview.issue_id == iss.id).first()
        doc = db.query(Document).filter(Document.id == iss.document_id).first() if iss.document_id else None
        issue_items.append({
            "id": iss.id,
            "verification_id": iss.verification_id,
            "document_id": iss.document_id,
            "document_name": iss.document_name or (doc.original_filename if doc else "N/A"),
            "page_number": iss.page_number or 1,
            "title": iss.title,
            "category": iss.category,
            "severity": iss.severity,
            "evidence_snippet": iss.evidence_snippet,
            "expected_value": iss.expected_value,
            "actual_value": iss.actual_value,
            "explanation": iss.explanation,
            "rag_rule_id": iss.rag_rule_id,
            "suggested_correction": iss.suggested_correction,
            "review_status": rev.decision if rev else "Pending Human Review",
            "reviewer_notes": rev.admin_notes if rev else None,
            "created_at": iss.created_at
        })

    # 2. Submitted applications awaiting assessment
    submitted_apps = db.query(Application).filter(
        Application.status.in_(["Submitted", "Under Review", "Needs Review", "Flagged"])
    ).order_by(Application.created_at.desc()).limit(50).all()

    app_items = [
        {
            "id": a.id,
            "application_number": a.application_number,
            "title": a.title,
            "scholarship_name": a.scholarship_name,
            "status": a.status,
            "applicant_email": a.user.email if a.user else "N/A",
            "document_count": len(a.documents),
            "submitted_at": a.submitted_at,
            "created_at": a.created_at
        }
        for a in submitted_apps
    ]

    return {
        "reviewer_id": current_reviewer.id,
        "reviewer_email": current_reviewer.email,
        "total_flagged_issues": len(issue_items),
        "total_pending_applications": len(app_items),
        "flagged_issues": issue_items,
        "pending_applications": app_items
    }

@router.post("/issues/{issue_id}/decision")
def record_issue_review_decision(
    issue_id: int,
    decision_in: ReviewDecisionRequest,
    current_reviewer: User = Depends(get_current_reviewer),
    db: Session = Depends(get_db)
):
    """
    Human Reviewer records decision on an AI verification finding:
    - Decisions: 'approved', 'rejected', 'override_pass', 'request_info'
    - Preserves original AI finding intact
    - Records human decision, reviewer notes, and timestamp
    - Emits audit log and user notification
    """
    valid_decisions = ["approved", "rejected", "override_pass", "request_info"]
    decision = decision_in.decision.lower().strip()
    if decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision '{decision}'. Must be one of: {', '.join(valid_decisions)}"
        )

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")

    # Check for existing review record
    existing_rev = db.query(AdminReview).filter(AdminReview.issue_id == issue.id).first()
    prev_status = existing_rev.decision if existing_rev else "Pending"

    if existing_rev:
        existing_rev.previous_status = prev_status
        existing_rev.decision = decision
        existing_rev.new_status = decision
        existing_rev.admin_notes = decision_in.reviewer_comments or "Reviewed by human evaluator."
        existing_rev.admin_id = current_reviewer.id
        existing_rev.reviewed_at = datetime.datetime.utcnow()
    else:
        new_rev = AdminReview(
            issue_id=issue.id,
            admin_id=current_reviewer.id,
            decision=decision,
            previous_status="Pending",
            new_status=decision,
            admin_notes=decision_in.reviewer_comments or "Reviewed by human evaluator.",
            reviewed_at=datetime.datetime.utcnow()
        )
        db.add(new_rev)

    # Log audit entry
    audit = AuditLog(
        user_id=current_reviewer.id,
        action="REVIEWER_DECISION",
        target_type="issue",
        target_id=issue.id,
        details=f"Reviewer recorded '{decision}' on Issue #{issue.id} ({issue.title}). Notes: {decision_in.reviewer_comments or 'None'}"
    )
    db.add(audit)

    # If linked to user via verification, send notification
    if issue.verification and issue.verification.user_id:
        notif = Notification(
            user_id=issue.verification.user_id,
            title="Human Review Decision Recorded",
            message=f"Reviewer evaluated issue '{issue.title}' on {issue.document_name}: Decision '{decision.upper()}'. Comments: {decision_in.reviewer_comments or 'None'}",
            category="info" if decision != "rejected" else "warning",
            link=f"/evidence/{issue.id}"
        )
        db.add(notif)

    db.commit()

    return {
        "message": f"Review decision '{decision}' recorded successfully.",
        "issue_id": issue.id,
        "decision": decision,
        "reviewer": current_reviewer.email
    }

@router.post("/applications/{application_id}/status")
def update_application_review_status(
    application_id: int,
    status_label: str,
    reviewer_notes: Optional[str] = None,
    current_reviewer: User = Depends(get_current_reviewer),
    db: Session = Depends(get_db)
):
    """Update overall application assessment status: 'Under Review', 'Verified', 'Needs Review', 'Flagged'."""
    app_obj = db.query(Application).filter(Application.id == application_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found.")

    valid_statuses = ["Draft", "Submitted", "Under Review", "Verified", "Needs Review", "Flagged"]
    if status_label not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    app_obj.status = status_label
    app_obj.assigned_reviewer_id = current_reviewer.id
    if reviewer_notes:
        app_obj.reviewer_notes = reviewer_notes

    # Audit log
    audit = AuditLog(
        user_id=current_reviewer.id,
        action="UPDATE_APPLICATION_STATUS",
        target_type="application",
        target_id=app_obj.id,
        details=f"Reviewer updated application {app_obj.application_number} status to '{status_label}'"
    )
    db.add(audit)

    # Notification to applicant
    notif = Notification(
        user_id=app_obj.user_id,
        title=f"Application Status: {status_label}",
        message=f"Your scholarship application {app_obj.application_number} has been updated to '{status_label}'. Reviewer notes: {reviewer_notes or 'None'}",
        category="success" if status_label == "Verified" else ("warning" if status_label in ("Flagged", "Needs Review") else "info"),
        link=f"/applications/{app_obj.id}"
    )
    db.add(notif)
    db.commit()

    return {"message": "Application status updated.", "application_id": app_obj.id, "new_status": app_obj.status}
