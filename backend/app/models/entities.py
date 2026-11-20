import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="student", nullable=False)  # student or admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    verifications = relationship("VerificationResult", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    admin_reviews = relationship("AdminReview", back_populates="admin")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    readiness_scores = relationship("ReadinessScore", back_populates="user", cascade="all, delete-orphan")
    chat_conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("ApplicantProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan", foreign_keys="[Application.user_id]")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    upload_status = Column(String(50), default="uploaded", nullable=False)  # uploaded, processed, failed
    image_quality_score = Column(Float, default=1.0)
    is_blurry = Column(Boolean, default=False)
    is_low_res = Column(Boolean, default=False)
    is_rotated = Column(Boolean, default=False)
    page_count = Column(Integer, default=1)
    raw_text = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    language = Column(String(50), default="eng", nullable=False)  # eng, tel, mixed
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    application = relationship("Application", back_populates="documents")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="document")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    readiness_scores = relationship("ReadinessScore", back_populates="document", cascade="all, delete-orphan")

    @property
    def quality_score(self) -> float:
        return self.image_quality_score if self.image_quality_score is not None else 1.0


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    quality_score = Column(Float, default=1.0)
    change_summary = Column(Text, nullable=True)
    extracted_fields_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="versions")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    field_value = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    page_number = Column(Integer, default=1)
    extraction_method = Column(String(50), default="regex")  # regex, layout, nlp
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_width = Column(Float, nullable=True)
    bbox_height = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="extracted_fields")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    verification_mode = Column(String(50), nullable=False)  # single, multiple
    document_ids = Column(Text, nullable=False)  # JSON serialized list of document IDs
    overall_status = Column(String(50), nullable=False, index=True)
    # Statuses: 'Passed', 'Passed with Warnings', 'Needs Correction', 'Manual Review Required', 'Processing Failed'
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    readiness_score = Column(Integer, default=100)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="verifications")
    issues = relationship("Issue", back_populates="verification", cascade="all, delete-orphan")
    cross_comparisons = relationship("CrossDocumentComparison", back_populates="verification", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="verification", cascade="all, delete-orphan")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verification_results.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    # Categories: missing_field, invalid_date, mismatch, quality, expiry, structure, signature_stamp, duplicate, format
    severity = Column(String(50), nullable=False)  # critical, high, medium, low, info
    document_name = Column(String(255), nullable=True)
    page_number = Column(Integer, default=1)
    evidence_snippet = Column(Text, nullable=True)
    expected_value = Column(String(255), nullable=True)
    actual_value = Column(String(255), nullable=True)
    explanation = Column(Text, nullable=False)
    suggested_correction = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    manual_review_recommended = Column(Boolean, default=False)
    rag_rule_id = Column(String(100), nullable=True)
    rag_source = Column(String(255), nullable=True)
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_width = Column(Float, nullable=True)
    bbox_height = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    verification = relationship("VerificationResult", back_populates="issues")
    document = relationship("Document", back_populates="issues")
    admin_reviews = relationship("AdminReview", back_populates="issue")


class CrossDocumentComparison(Base):
    __tablename__ = "cross_document_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verification_results.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    doc_a_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    doc_b_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    doc_a_name = Column(String(255), nullable=False)
    doc_b_name = Column(String(255), nullable=False)
    val_a = Column(Text, nullable=True)
    val_b = Column(Text, nullable=True)
    is_match = Column(Boolean, nullable=False)
    similarity_score = Column(Float, default=1.0)
    difference_explanation = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    verification = relationship("VerificationResult", back_populates="cross_comparisons")


class VerificationRule(Base):
    __tablename__ = "verification_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(100), unique=True, index=True, nullable=False)
    document_category = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    mandatory_fields = Column(Text, nullable=False)  # JSON list string
    validity_period_months = Column(Integer, default=0)  # 0 = permanent/no expiry
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ReferenceMaterial(Base):
    __tablename__ = "reference_materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=False)
    authority = Column(String(255), default="Government Authority")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class AdminReview(Base):
    __tablename__ = "admin_reviews"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    decision = Column(String(50), nullable=False)  # approved, rejected, override_pass, requires_resubmission
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    admin_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    issue = relationship("Issue", back_populates="admin_reviews")
    admin = relationship("User", back_populates="admin_reviews")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # UPLOAD, VERIFY, ADMIN_DECISION, UPDATE_RULE, etc.
    target_type = Column(String(100), nullable=True)  # document, verification, rule, user
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON or text description
    ip_address = Column(String(50), default="127.0.0.1")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")


class ReadinessScore(Base):
    __tablename__ = "readiness_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    score = Column(Integer, nullable=False)  # 0 to 100
    completeness_score = Column(Integer, default=100)
    quality_score = Column(Integer, default=100)
    validation_score = Column(Integer, default=100)
    deductions_json = Column(Text, nullable=True)  # JSON array of deductions with reasons
    breakdown_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="readiness_scores")
    document = relationship("Document", back_populates="readiness_scores")


class ScholarshipRequirement(Base):
    __tablename__ = "scholarship_requirements"

    id = Column(Integer, primary_key=True, index=True)
    scholarship_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    required_categories = Column(Text, nullable=False)  # JSON array of categories
    min_readiness_score = Column(Integer, default=75)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verification_results.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_uuid = Column(String(100), unique=True, index=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    verification = relationship("VerificationResult", back_populates="reports")
    user = relationship("User", back_populates="reports")


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), default="Document Assistant Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False, index=True)
    sender = Column(String(50), nullable=False)  # user, assistant
    message = Column(Text, nullable=False)
    evidence_references = Column(Text, nullable=True)  # JSON array of cited document names and pages
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    conversation = relationship("ChatConversation", back_populates="messages")


class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    institution_name = Column(String(255), nullable=True)
    degree_program = Column(String(100), nullable=True)
    enrollment_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="profile")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    application_number = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    scholarship_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="Draft", nullable=False)  # Draft, Submitted, Under Review, Verified, Flagged, Needs Review
    academic_year = Column(String(50), default="2025-2026")
    notes = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    assigned_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="applications", foreign_keys=[user_id])
    documents = relationship("Document", back_populates="application")


class Guideline(Base):
    __tablename__ = "guidelines"

    id = Column(Integer, primary_key=True, index=True)
    guideline_code = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    issuing_authority = Column(String(255), default="Government Authority", nullable=False)
    category = Column(String(100), nullable=False, index=True)
    source_url = Column(String(500), nullable=True)
    version = Column(String(50), default="1.0", nullable=False)
    effective_from = Column(String(50), nullable=True)
    effective_to = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    is_approved = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="info", nullable=False)  # info, warning, success, alert
    link = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    category = Column(String(100), default="Verification Question", nullable=False)
    priority = Column(String(50), default="Medium", nullable=False)  # Low, Medium, High, Urgent
    status = Column(String(50), default="Open", nullable=False)  # Open, In Progress, Resolved, Closed
    message = Column(Text, nullable=False)
    admin_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="support_tickets")

