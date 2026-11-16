import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Document, VerificationResult, Issue, CrossDocumentComparison, User
from backend.app.schemas.verification import (
    MultipleVerificationRequest, VerificationResponse, VerificationHistoryItem, IssueSchema, ComparisonSchema
)
from backend.app.core.dependencies import get_current_user
from backend.app.services.verification.single_verifier import SingleDocumentVerifier
from backend.app.services.verification.cross_verifier import CrossDocumentVerifier

router = APIRouter(prefix="/verify", tags=["Verification"])

@router.post("/document/{document_id}", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
def verify_single_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Run Single Document Verification
    result_data = SingleDocumentVerifier.verify_document(doc, db)

    # Save to database
    verification_record = VerificationResult(
        user_id=current_user.id,
        verification_mode="single",
        document_ids=json.dumps([doc.id]),
        overall_status=result_data["overall_status"],
        total_issues=result_data["total_issues"],
        critical_issues=result_data["critical_issues"],
        warning_issues=result_data["warning_issues"],
        summary=result_data["summary"]
    )
    db.add(verification_record)
    db.commit()
    db.refresh(verification_record)

    # Save issues
    issue_models = []
    for iss in result_data["issues"]:
        issue_model = Issue(
            verification_id=verification_record.id,
            document_id=doc.id,
            title=iss["title"],
            category=iss["category"],
            severity=iss["severity"],
            document_name=iss["document_name"],
            page_number=iss["page_number"],
            evidence_snippet=iss["evidence_snippet"],
            expected_value=iss["expected_value"],
            actual_value=iss["actual_value"],
            explanation=iss["explanation"],
            suggested_correction=iss["suggested_correction"],
            confidence_score=iss["confidence_score"],
            manual_review_recommended=iss["manual_review_recommended"],
            rag_rule_id=iss["rag_rule_id"],
            rag_source=iss["rag_source"]
        )
        db.add(issue_model)
        issue_models.append(issue_model)

    db.commit()
    db.refresh(verification_record)

    return VerificationResponse(
        id=verification_record.id,
        verification_mode=verification_record.verification_mode,
        document_ids=[doc.id],
        overall_status=verification_record.overall_status,
        total_issues=verification_record.total_issues,
        critical_issues=verification_record.critical_issues,
        warning_issues=verification_record.warning_issues,
        summary=verification_record.summary,
        created_at=verification_record.created_at,
        issues=[IssueSchema.from_orm(im) for im in issue_models],
        cross_comparisons=[]
    )

@router.post("/multiple", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
def verify_multiple_documents(
    payload: MultipleVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if len(payload.document_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multi-document cross-verification requires at least two document IDs."
        )

    docs = db.query(Document).filter(Document.id.in_(payload.document_ids)).all()
    if len(docs) != len(payload.document_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more specified documents could not be found."
        )

    # Verify user ownership
    for doc in docs:
        if doc.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to document '{doc.original_filename}'."
            )

    # Run Cross-Verification
    result_data = CrossDocumentVerifier.verify_multiple(docs, db)

    # Save to database
    verification_record = VerificationResult(
        user_id=current_user.id,
        verification_mode="multiple",
        document_ids=json.dumps([d.id for d in docs]),
        overall_status=result_data["overall_status"],
        total_issues=result_data["total_issues"],
        critical_issues=result_data["critical_issues"],
        warning_issues=result_data["warning_issues"],
        summary=result_data["summary"]
    )
    db.add(verification_record)
    db.commit()
    db.refresh(verification_record)

    # Save issues
    issue_models = []
    for iss in result_data["issues"]:
        issue_model = Issue(
            verification_id=verification_record.id,
            document_id=None,
            title=iss["title"],
            category=iss["category"],
            severity=iss["severity"],
            document_name=iss["document_name"],
            page_number=iss["page_number"],
            evidence_snippet=iss["evidence_snippet"],
            expected_value=iss["expected_value"],
            actual_value=iss["actual_value"],
            explanation=iss["explanation"],
            suggested_correction=iss["suggested_correction"],
            confidence_score=iss["confidence_score"],
            manual_review_recommended=iss["manual_review_recommended"],
            rag_rule_id=iss["rag_rule_id"],
            rag_source=iss["rag_source"]
        )
        db.add(issue_model)
        issue_models.append(issue_model)

    # Save cross document comparisons
    comparison_models = []
    for cmp in result_data["comparisons"]:
        comp_model = CrossDocumentComparison(
            verification_id=verification_record.id,
            field_name=cmp["field_name"],
            doc_a_id=cmp["doc_a_id"],
            doc_b_id=cmp["doc_b_id"],
            doc_a_name=cmp["doc_a_name"],
            doc_b_name=cmp["doc_b_name"],
            val_a=cmp["val_a"],
            val_b=cmp["val_b"],
            is_match=cmp["is_match"],
            similarity_score=cmp["similarity_score"],
            difference_explanation=cmp["difference_explanation"],
            recommendation=cmp["recommendation"]
        )
        db.add(comp_model)
        comparison_models.append(comp_model)

    db.commit()
    db.refresh(verification_record)

    return VerificationResponse(
        id=verification_record.id,
        verification_mode=verification_record.verification_mode,
        document_ids=[d.id for d in docs],
        overall_status=verification_record.overall_status,
        total_issues=verification_record.total_issues,
        critical_issues=verification_record.critical_issues,
        warning_issues=verification_record.warning_issues,
        summary=verification_record.summary,
        created_at=verification_record.created_at,
        issues=[IssueSchema.from_orm(im) for im in issue_models],
        cross_comparisons=[ComparisonSchema.from_orm(cm) for cm in comparison_models]
    )

@router.get("/history", response_model=List[VerificationHistoryItem])
def get_verification_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = db.query(VerificationResult).filter(
        VerificationResult.user_id == current_user.id
    ).order_by(VerificationResult.created_at.desc()).all()

    history = []
    for r in results:
        doc_ids = []
        try:
            doc_ids = json.loads(r.document_ids)
        except Exception:
            pass
        history.append(VerificationHistoryItem(
            id=r.id,
            verification_mode=r.verification_mode,
            document_ids=doc_ids,
            overall_status=r.overall_status,
            total_issues=r.total_issues,
            critical_issues=r.critical_issues,
            warning_issues=r.warning_issues,
            summary=r.summary or "",
            created_at=r.created_at
        ))
    return history

@router.get("/{verification_id}", response_model=VerificationResponse)
def get_verification_detail(
    verification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    v = db.query(VerificationResult).filter(VerificationResult.id == verification_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found.")

    if v.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    doc_ids = []
    try:
        doc_ids = json.loads(v.document_ids)
    except Exception:
        pass

    return VerificationResponse(
        id=v.id,
        verification_mode=v.verification_mode,
        document_ids=doc_ids,
        overall_status=v.overall_status,
        total_issues=v.total_issues,
        critical_issues=v.critical_issues,
        warning_issues=v.warning_issues,
        summary=v.summary or "",
        created_at=v.created_at,
        issues=[IssueSchema.from_orm(im) for im in v.issues],
        cross_comparisons=[ComparisonSchema.from_orm(cm) for cm in v.cross_comparisons]
    )

@router.post("/{verification_id}/recheck", response_model=VerificationResponse)
def recheck_verification(
    verification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    v = db.query(VerificationResult).filter(VerificationResult.id == verification_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found.")

    if v.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    doc_ids = []
    try:
        doc_ids = json.loads(v.document_ids)
    except Exception:
        pass

    if v.verification_mode == "single" and len(doc_ids) == 1:
        return verify_single_document(document_id=doc_ids[0], current_user=current_user, db=db)
    else:
        return verify_multiple_documents(payload=MultipleVerificationRequest(document_ids=doc_ids), current_user=current_user, db=db)
