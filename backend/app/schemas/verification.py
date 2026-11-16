from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class IssueSchema(BaseModel):
    id: Optional[int] = None
    title: str
    category: str
    severity: str
    document_name: Optional[str] = None
    page_number: int = 1
    evidence_snippet: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    explanation: str
    suggested_correction: str
    confidence_score: float = 1.0
    manual_review_recommended: bool = False
    rag_rule_id: Optional[str] = None
    rag_source: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ComparisonSchema(BaseModel):
    id: Optional[int] = None
    field_name: str
    doc_a_id: int
    doc_b_id: int
    doc_a_name: str
    doc_b_name: str
    val_a: Optional[str] = None
    val_b: Optional[str] = None
    is_match: bool
    similarity_score: float
    difference_explanation: Optional[str] = None
    recommendation: Optional[str] = None

    class Config:
        from_attributes = True

class MultipleVerificationRequest(BaseModel):
    document_ids: List[int]

class VerificationResponse(BaseModel):
    id: int
    verification_mode: str
    document_ids: List[int]
    overall_status: str
    total_issues: int
    critical_issues: int
    warning_issues: int
    summary: str
    created_at: datetime
    issues: List[IssueSchema] = []
    cross_comparisons: List[ComparisonSchema] = []

    class Config:
        from_attributes = True

class VerificationHistoryItem(BaseModel):
    id: int
    verification_mode: str
    document_ids: List[int]
    overall_status: str
    total_issues: int
    critical_issues: int
    warning_issues: int
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True
