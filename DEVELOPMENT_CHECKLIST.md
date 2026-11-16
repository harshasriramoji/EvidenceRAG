# EvidenceRAG Master Project Development Checklist

## Project Information
- **Project Title:** EvidenceRAG: Explainable Pre-Submission Application Verification Using Retrieval-Augmented Generation
- **Target Audience:** Actual registered students verifying scholarship application documents before submission; Administrators reviewing rules & flagged documents.
- **Verification Modes:**
  - Mode A: Single Document Verification (20+ automated checks)
  - Mode B: Multiple Document Cross-Verification (Cross-document entity matrix)
- **Status:** Complete (100% Real End-to-End Implementation, 25/25 Automated Tests Passing across 22 Frontend Pages and 16 Database Tables)

---

## Phase Breakdown & Status

### Phase 1: Project Setup, Folder Structure, Frontend & Backend Connection [COMPLETED]
- [x] Python 3.13 and Node environment inspected and verified.
- [x] Clean directory structure established (`backend/`, `frontend/`, `models/`, `scripts/`, `storage/`).
- [x] No preloaded sample user documents or fictional applicant dataset directories in production.
- [x] Backend FastAPI application configured with CORS, health check, unified router.
- [x] Frontend React 19 + Vite + TypeScript + Tailwind CSS configured and built into `frontend/dist/`.
- [x] Unified single-server mounting verified (FastAPI serves both `/api/*` and `frontend/dist`).
- [x] High-contrast professional palette implemented across all 22 pages (`#F8FAFF` background, `#0F172A` text, `#475569` subtext, `#2563EB` primary blue, `#1D4ED8` dark blue, `#DBEAFE` light blue, `#EFF6FF` pale blue, `#CBD5E1` borders).

### Phase 2: Database, Email Registration, Login, JWT & Role-Based Access [COMPLETED]
- [x] SQLAlchemy models with 16 relational tables: `users`, `documents`, `document_versions`, `extracted_fields`, `verification_results`, `issues`, `cross_document_comparisons`, `verification_rules`, `reference_materials`, `admin_reviews`, `audit_logs`, `readiness_scores`, `scholarship_requirements`, `reports`, `chat_conversations`, `chat_messages`.
- [x] Clean database initialization with zero fake users or preloaded verification results (`backend/app/database/init_db.py`).
- [x] Registration Form: Simplified to Email, Account Role dropdown (`Student / Scholarship Applicant`, `Administrator`), and Password with Show/Hide toggle. Full Legal Name and Confirm Password removed.
- [x] Administrator Authorization Security: Selecting "Administrator" requires a valid administrator authorization code (`AdminSecret@2026`) to prevent unauthorized admin creation; unauthenticated admin registrations are rejected with 403 Forbidden.
- [x] Sign In page with email and password, show/hide password toggle, and no hardcoded demo accounts.
- [x] Case-insensitive email comparison for login and registration.
- [x] Role-Based Redirection: Successful login as student navigates to `/dashboard`; login as admin navigates directly to `/admin`.
- [x] Stateless JWT token issuance and route protection (`/api/auth/me`).
- [x] Role-based access control (`student` vs `admin`).
- [x] Secure development-only admin creation script (`scripts/seed_admin.py`).

### Phase 3: Document Upload, Storage, Preview & OCR [COMPLETED]
- [x] Support for PDF, JPG, JPEG, and PNG formats.
- [x] Document categories: Aadhaar Card, Income Certificate, Caste Certificate, Residence Certificate, Study Certificate, Bonafide Certificate, Marks Memo, Bank Passbook, Passport Photo, Other Supporting Documents.
- [x] Multi-file validation: file extension, MIME type, max file size (15MB), empty (0-byte) file rejection, duplicate upload rejection.
- [x] Path traversal protection via unique safe UUID filenames.
- [x] Strict user-level document ownership: documents belong only to the logged-in user.
- [x] OpenCV document enhancement pipeline: grayscale conversion, noise removal, CLAHE contrast enhancement, deskewing, and adaptive binarization.
- [x] PyMuPDF native text extraction for digital PDFs; PyTesseract integration for image scans with graceful offline fallback.
- [x] Computer vision quality analysis: Laplacian focus variance blur detection ($\sigma^2 < 95$), resolution check, orientation detection.
- [x] Field extraction engine: Full name, DOB, certificate number, issue date, expiry date, address, income, caste, academic info.

### Phase 4: Single-Document Verification (Mode A) [COMPLETED]
- [x] Independent single-document audit without requiring any other document.
- [x] 20+ automated verification checks implemented.
- [x] Detection of missing mandatory fields, missing/placeholder names (`N/A`).
- [x] Invalid and impossible date checks (e.g. Feb 30, future dates).
- [x] Expiry detection based on configured validity rules (e.g. 12-month limit for Income Certificate).
- [x] Detection of image blur, low DPI, rotation, cropped text, blank pages, and category mismatch.
- [x] Unreadable OCR output detection ($<25$ characters).
- [x] Strict safety constraint: Never declares a document fake or fraudulent based on AI suspicion.
- [x] Issue details: Title, category, severity, page, evidence snippet, actual value, expected value, RAG explanation, suggested correction, confidence score, manual review recommendation.
- [x] Endpoint: `POST /api/verify/document/{id}`.

### Phase 5: Multiple-Document Cross-Verification (Mode B) [COMPLETED]
- [x] Batch verification of 2 to 10+ documents uploaded together.
- [x] Shared entity correlation: Full name, DOB, address, income amount, certificate number, institution, academic year, issue date.
- [x] Fuzzy token-sort ratio with configurable similarity thresholds ($0.85$ default) to tolerate benign formatting/spacing/casing/honorific differences.
- [x] Conflict detection, difference explanation, and suggested correction.
- [x] Consolidated status calculation and storage in `cross_document_comparisons` table.
- [x] Endpoint: `POST /api/verify/multiple`.

### Phase 6: Machine-Learning Module [COMPLETED]
- [x] Supervised TF-IDF + Logistic Regression document classifier.
- [x] Model persistence in `models/document_classifier.joblib`.
- [x] Evaluation metrics script (`scripts/train_classifier.py`) supporting user-provided labeled datasets.
- [x] Rule-based heuristic fallback across all categories when running without a pre-trained model.

### Phase 7: RAG Pipeline & Open-Source LLM Integration [COMPLETED]
- [x] Administrative reference knowledge base of 11 official regulatory rules kept strictly separate from user documents (`backend/app/services/rag/knowledge_base.py`).
- [x] Vector retrieval using TF-IDF cosine similarity with category-specific score boosting.
- [x] Optional Ollama LLM integration (compatible with Qwen / Llama).
- [x] Deterministic policy-grounded explanation generator for 100% offline operational reliability when Ollama is unavailable.
- [x] Grounded explanations citing exact policy sources and rule IDs.
- [x] Live interactive RAG semantic retrieval tester and policy manager in Admin panel (`/admin/knowledge-base`).

### Phase 8: Complete 22 Frontend Pages & Specialized Capabilities [COMPLETED]
- [x] Student Dashboard displaying metrics derived exclusively from actual database records for the logged-in user.
- [x] Clean zero-state with a helpful empty state when a student has not uploaded any documents.
- [x] Interactive status distribution charts using Recharts.
- [x] Document details page with document preview, extracted fields grid, OCR confidence, and issue breakdown.
- [x] Verification history page and re-check action (`POST /api/verify/{id}/recheck`).
- [x] Evidence Highlighting Viewer (`/evidence/:issueId`) with bounding box overlay and policy explanations.
- [x] Smart Side-by-Side Document Comparison (`/compare`) with interactive field discrepancy highlights.
- [x] Transparent Application Readiness Score Engine (`/readiness`) (0-100 scale, weighted components, deduction audit trail).
- [x] Scholarship Application Checklist (`/checklist`) with scheme selector and required certificate progress bar.
- [x] Ask Your Document AI Assistant (`/assistant`) with grounded citations and deterministic fallback.
- [x] Document Version History (`/documents/:id/versions`) with revision timeline and re-submission flow.
- [x] Admin Dashboard displaying platform-wide statistics (users, documents, verifications, status counts).
- [x] Flagged issues review queue with Approve / Reject / Override Pass decisions.
- [x] Administrative Audit Trail (`/admin/audit-logs`) with chronological system event logging.
- [x] Verification rules management page with live threshold and validity period editing.
- [x] Reference Knowledge Base Management Page (`/admin/knowledge-base`) for viewing, searching, and testing RAG semantic retrieval across all 11 regulatory verification rules.

### Phase 9: PDF Report Generation (ReportLab) [COMPLETED]
- [x] Branded ReportLab PDF document layout.
- [x] Single-document verification dossier.
- [x] Multi-document cross-verification combined report.
- [x] Tailored Pre-Submission Correction Checklist PDF (`POST /api/reports/correction-checklist`).
- [x] Structured issues table, extracted fields grid, RAG policy citations, and legal disclaimers.
- [x] Endpoints: `POST /api/reports/generate/{verification_id}`, `GET /api/reports/{report_id}/download`, `POST /api/reports/correction-checklist`.

### Phase 10: Security, Automated Testing, Bug Fixing & Documentation [COMPLETED]
- [x] User-level document isolation verified: User B cannot access, preview, or delete User A's documents or reports.
- [x] Path traversal protection and file sanitization.
- [x] Automated test suite in `backend/tests/test_end_to_end.py` and `test_health.py`: 25/25 tests passing 100%.
- [x] Dynamic test fixtures generated at runtime in isolated temp directories and cleaned up after execution.
- [x] Comprehensive root `README.md` with system architecture, 5 Mermaid diagrams, installation and execution instructions, and limitations.
