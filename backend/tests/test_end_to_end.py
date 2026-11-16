import os
import uuid
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.app.main import app
from backend.app.core.config import settings, BASE_DIR
from backend.app.services.rag.engine import rag_engine

client = TestClient(app)

def create_temp_pdf(content_lines: list, filename: str = "test_doc.pdf") -> str:
    """Generate a temporary PDF file for test fixtures."""
    tmp_dir = Path(tempfile.gettempdir()) / "evidencerag_test_fixtures"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    file_path = tmp_dir / f"{uuid.uuid4().hex}_{filename}"
    c = canvas.Canvas(str(file_path), pagesize=letter)
    y = 750
    for line in content_lines:
        c.drawString(72, y, line)
        y -= 25
    c.save()
    return str(file_path)

def create_blurry_image(filename: str = "blurry_scan.png") -> str:
    """Generate a heavily blurred image to test Laplacian blur detection."""
    tmp_dir = Path(tempfile.gettempdir()) / "evidencerag_test_fixtures"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    file_path = tmp_dir / f"{uuid.uuid4().hex}_{filename}"
    # Create smooth image with very low edge variance
    img = Image.new("RGB", (800, 1000), color=(240, 240, 240))
    # Apply Gaussian blur
    img = img.filter(ImageFilter.GaussianBlur(radius=15))
    img.save(str(file_path))
    return str(file_path)

@pytest.fixture(scope="module")
def admin_user():
    """Ensure an admin account exists and return auth headers."""
    admin_email = "admin@evidencerag.com"
    admin_pass = "Admin@12345"
    # Attempt login
    login_res = client.post("/api/auth/login", json={"email": admin_email, "password": admin_pass})
    if login_res.status_code != 200:
        # Register admin if not present
        client.post("/api/auth/register", json={
            "email": admin_email,
            "full_name": "System Administrator",
            "password": admin_pass,
            "role": "admin",
            "admin_code": "AdminSecret@2026"
        })
        login_res = client.post("/api/auth/login", json={"email": admin_email, "password": admin_pass})
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def student_user():
    """Register and login a dedicated student account for test suite."""
    email = f"student_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "StudentPassword@123"
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Ananya Verma",
        "password": pwd,
        "role": "student"
    })
    assert reg_res.status_code == 201
    login_res = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "email": email,
        "full_name": "Ananya Verma"
    }

# -------------------------------------------------------------
# 1. Health & Base System Tests
# -------------------------------------------------------------
def test_01_system_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

# -------------------------------------------------------------
# 2. Authentication, Validation, and RBAC
# -------------------------------------------------------------
def test_02_email_registration_and_duplicate_prevention():
    test_email = f"USER_{uuid.uuid4().hex[:6]}@DOMAIN.COM"  # test uppercase conversion
    payload = {
        "email": test_email,
        "full_name": "Test User",
        "password": "ValidPassword@123",
        "role": "student"
    }
    # 1. First registration should succeed
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == test_email.lower()

    # 2. Duplicate registration with same email (different case) must be rejected
    dup_res = client.post("/api/auth/register", json={**payload, "email": test_email.lower()})
    assert dup_res.status_code == 400
    assert "already registered" in dup_res.json()["detail"].lower()

    # 3. Weak password rejection
    weak_res = client.post("/api/auth/register", json={
        "email": f"weak_{uuid.uuid4().hex[:4]}@example.com",
        "full_name": "Weak User",
        "password": "123",
        "role": "student"
    })
    assert weak_res.status_code in (400, 422)

    # 4. Unauthorized admin registration without secret key must be rejected (403 Forbidden)
    unauth_admin = client.post("/api/auth/register", json={
        "email": f"fake_admin_{uuid.uuid4().hex[:4]}@example.com",
        "password": "ValidPassword@123",
        "role": "admin"
    })
    assert unauth_admin.status_code == 403
    assert "administrator authorization code" in unauth_admin.json()["detail"].lower()

    # 5. Admin registration with valid secret code succeeds
    valid_admin_email = f"auth_admin_{uuid.uuid4().hex[:4]}@example.com"
    auth_admin = client.post("/api/auth/register", json={
        "email": valid_admin_email,
        "password": "ValidPassword@123",
        "role": "admin",
        "admin_code": "AdminSecret@2026"
    })
    assert auth_admin.status_code == 201
    assert auth_admin.json()["role"] == "admin"

def test_03_login_validation_and_case_insensitivity():
    email = f"case_test_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "SecretPassword@123"
    client.post("/api/auth/register", json={"email": email, "full_name": "Case Test", "password": pwd, "role": "student"})

    # Login with mixed case email
    res = client.post("/api/auth/login", json={"email": email.upper(), "password": pwd})
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Incorrect password rejection
    wrong_pwd_res = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword"})
    assert wrong_pwd_res.status_code == 401

    # Unregistered email rejection
    unreg_res = client.post("/api/auth/login", json={"email": "nonexistent_9999@example.com", "password": "AnyPassword@123"})
    assert unreg_res.status_code == 401

def test_04_role_based_access_control(student_user, admin_user):
    # Student cannot access admin dashboard
    student_headers = student_user["headers"]
    forbidden_res = client.get("/api/admin/dashboard", headers=student_headers)
    assert forbidden_res.status_code == 403

    # Admin can access admin dashboard
    admin_ok_res = client.get("/api/admin/dashboard", headers=admin_user)
    assert admin_ok_res.status_code == 200
    data = admin_ok_res.json()
    assert "total_users" in data
    assert "total_documents" in data

# -------------------------------------------------------------
# 3. Document Upload Validation
# -------------------------------------------------------------
def test_05_document_upload_and_validation(student_user):
    student_headers = student_user["headers"]

    # 1. Invalid file extension rejection
    res_invalid_ext = client.post(
        "/api/documents/upload",
        headers=student_headers,
        files=[("files", ("test.exe", b"fake binary executable content", "application/x-msdownload"))],
        data={"category": "Aadhaar Card"}
    )
    assert res_invalid_ext.status_code in (400, 422)

    # 2. Empty file rejection
    res_empty = client.post(
        "/api/documents/upload",
        headers=student_headers,
        files=[("files", ("empty.pdf", b"", "application/pdf"))],
        data={"category": "Aadhaar Card"}
    )
    assert res_empty.status_code in (400, 422)

    # 3. Valid document upload
    valid_pdf = create_temp_pdf([
        "GOVERNMENT OF INDIA - UNIQUE IDENTIFICATION AUTHORITY",
        "Document Type: Aadhaar Card",
        "Certificate No: CERT-2026-88123",
        "Date of Issue: 10/05/2026",
        "Full Name: Ananya Verma",
        "Date of Birth: 24/01/2001",
        "Gender: Female",
        "Aadhaar Number: 8901 5846 5798",
        "Permanent Address: H.No 50, Bengaluru - 500092",
        "Official Departmental Seal Attached"
    ], filename="aadhaar_ananya.pdf")

    with open(valid_pdf, "rb") as f:
        up_res = client.post(
            "/api/documents/upload",
            headers=student_headers,
            files=[("files", ("aadhaar_ananya.pdf", f, "application/pdf"))],
            data={"category": "Aadhaar Card"}
        )
    assert up_res.status_code == 201
    docs = up_res.json()
    assert len(docs) == 1
    doc_id = docs[0]["id"]
    assert doc_id > 0
    assert docs[0]["category"] == "Aadhaar Card"

    # 4. Duplicate upload rejection
    with open(valid_pdf, "rb") as f:
        dup_up_res = client.post(
            "/api/documents/upload",
            headers=student_headers,
            files=[("files", ("aadhaar_ananya.pdf", f, "application/pdf"))],
            data={"category": "Aadhaar Card"}
        )
    assert dup_up_res.status_code == 400
    assert "duplicate" in dup_up_res.json()["detail"].lower()

# -------------------------------------------------------------
# 4. User Access Isolation Security
# -------------------------------------------------------------
def test_06_user_document_isolation(student_user):
    # Upload document under student A
    pdf_path = create_temp_pdf(["Confidential Applicant Document", "Name: Ananya Verma"], "private_doc.pdf")
    with open(pdf_path, "rb") as f:
        u_res = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("private_doc.pdf", f, "application/pdf"))],
            data={"category": "Other Supporting Documents"}
        )
    doc_id = u_res.json()[0]["id"]

    # Register student B
    b_email = f"user_b_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/auth/register", json={"email": b_email, "full_name": "User B", "password": "Password@123", "role": "student"})
    b_token = client.post("/api/auth/login", json={"email": b_email, "password": "Password@123"}).json()["access_token"]
    user_b_headers = {"Authorization": f"Bearer {b_token}"}

    # Student B attempts to access Student A's document -> 403 Forbidden
    get_res = client.get(f"/api/documents/{doc_id}", headers=user_b_headers)
    assert get_res.status_code in (403, 404)

    # Student B attempts to delete Student A's document -> 403 Forbidden
    del_res = client.delete(f"/api/documents/{doc_id}", headers=user_b_headers)
    assert del_res.status_code in (403, 404)

# -------------------------------------------------------------
# 5. Single Document Verification (Mode A)
# -------------------------------------------------------------
def test_07_single_verify_valid_document(student_user):
    # Upload clean Caste Certificate
    caste_pdf = create_temp_pdf([
        "GOVERNMENT REVENUE DEPARTMENT",
        "Document Type: Caste Certificate",
        "Certificate No: CERT-2026-99321",
        "Date of Issue: 12/04/2026",
        "Full Name: Ananya Verma",
        "Caste Category: SC",
        "Permanent Address: H.No 50, Bengaluru",
        "Official Seal Attached"
    ], "valid_caste.pdf")

    with open(caste_pdf, "rb") as f:
        up = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("valid_caste.pdf", f, "application/pdf"))],
            data={"category": "Caste Certificate"}
        )
    doc_id = up.json()[0]["id"]

    # Run Single Verification
    v_res = client.post(f"/api/verify/document/{doc_id}", headers=student_user["headers"])
    assert v_res.status_code == 201
    v_data = v_res.json()
    assert v_data["overall_status"] in ("Passed", "Passed with Warnings", "Manual Review Required")
    assert v_data.get("critical_issues", 0) == 0

def test_08_single_verify_missing_fields_detection(student_user):
    # Upload document with missing applicant name
    missing_pdf = create_temp_pdf([
        "GOVERNMENT REVENUE DEPARTMENT",
        "Document Type: Aadhaar Card",
        "Certificate No: CERT-2026-44112",
        "Date of Issue: 10/05/2026",
        "Full Name: N/A",
        "Date of Birth: 24/01/2001",
        "Gender: Female",
        "Aadhaar Number: 9912 3341 5521"
    ], "missing_name_aadhaar.pdf")

    with open(missing_pdf, "rb") as f:
        up = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("missing_name_aadhaar.pdf", f, "application/pdf"))],
            data={"category": "Aadhaar Card"}
        )
    doc_id = up.json()[0]["id"]

    v_res = client.post(f"/api/verify/document/{doc_id}", headers=student_user["headers"])
    assert v_res.status_code == 201
    v_data = v_res.json()
    assert v_data["overall_status"] in ("Needs Correction", "Manual Review Required")
    assert len(v_data["issues"]) > 0
    # Confirm issue metadata
    issue = v_data["issues"][0]
    assert "title" in issue
    assert "explanation" in issue
    assert "suggested_correction" in issue

def test_09_single_verify_blurry_scan_detection(student_user):
    # Upload heavily blurred image scan
    blur_img = create_blurry_image("blurry_id.png")
    with open(blur_img, "rb") as f:
        up = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("blurry_id.png", f, "image/png"))],
            data={"category": "Aadhaar Card"}
        )
    doc_id = up.json()[0]["id"]

    v_res = client.post(f"/api/verify/document/{doc_id}", headers=student_user["headers"])
    assert v_res.status_code == 201
    v_data = v_res.json()
    # Quality analysis should flag blur or trigger manual review
    assert v_data["overall_status"] in ("Manual Review Required", "Needs Correction", "Passed with Warnings")

# -------------------------------------------------------------
# 6. Multiple Document Cross-Verification (Mode B)
# -------------------------------------------------------------
def test_10_cross_verification_matching_documents(student_user):
    # Upload Aadhaar
    p1 = create_temp_pdf([
        "Document Type: Aadhaar Card",
        "Certificate No: CERT-2026-1001",
        "Date of Issue: 01/01/2026",
        "Full Name: Ananya Verma",
        "Date of Birth: 24/01/2001",
        "Permanent Address: H.No 50, Bengaluru"
    ], "cross_m_aadhaar.pdf")
    with open(p1, "rb") as f:
        u1 = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("cross_m_aadhaar.pdf", f, "application/pdf"))],
            data={"category": "Aadhaar Card"}
        )
    # Upload Income Certificate with identical Name and DOB
    p2 = create_temp_pdf([
        "Document Type: Income Certificate",
        "Certificate No: CERT-2026-1002",
        "Date of Issue: 01/01/2026",
        "This is to certify that Sri/Kumari Ananya Verma Son/Daughter of Sri M. Verma",
        "residing at H.No 50, Bengaluru",
        "Annual Family Income: Rs. 95,000"
    ], "cross_m_income.pdf")
    with open(p2, "rb") as f:
        u2 = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("cross_m_income.pdf", f, "application/pdf"))],
            data={"category": "Income Certificate"}
        )

    id1, id2 = u1.json()[0]["id"], u2.json()[0]["id"]

    cross_res = client.post("/api/verify/multiple", headers=student_user["headers"], json={"document_ids": [id1, id2]})
    assert cross_res.status_code == 201
    c_data = cross_res.json()
    assert "cross_comparisons" in c_data

    # Verify that matching name has is_match = True
    name_matches = [c for c in c_data["cross_comparisons"] if c["field_name"] == "full_name"]
    if name_matches:
        assert name_matches[0]["is_match"] is True

def test_11_cross_verification_mismatch_detection(student_user):
    # Upload Aadhaar with Name: Ananya Verma
    p1 = create_temp_pdf([
        "Document Type: Aadhaar Card",
        "Certificate No: CERT-2026-2001",
        "Full Name: Ananya Verma",
        "Date of Birth: 24/01/2001"
    ], "mismatch_aadhaar.pdf")
    with open(p1, "rb") as f:
        u1 = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("mismatch_aadhaar.pdf", f, "application/pdf"))],
            data={"category": "Aadhaar Card"}
        )
    # Upload Income Certificate with deliberate name mismatch: Vikram Sharma
    p2 = create_temp_pdf([
        "Document Type: Income Certificate",
        "Certificate No: CERT-2026-2002",
        "This is to certify that Sri/Kumari Vikram Sharma",
        "residing at H.No 89, Chennai",
        "Annual Family Income: Rs. 80,000"
    ], "mismatch_income.pdf")
    with open(p2, "rb") as f:
        u2 = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("mismatch_income.pdf", f, "application/pdf"))],
            data={"category": "Income Certificate"}
        )

    id1, id2 = u1.json()[0]["id"], u2.json()[0]["id"]

    cross_res = client.post("/api/verify/multiple", headers=student_user["headers"], json={"document_ids": [id1, id2]})
    assert cross_res.status_code == 201
    c_data = cross_res.json()
    assert c_data["overall_status"] in ("Needs Correction", "Manual Review Required")
    mismatches = [c for c in c_data["cross_comparisons"] if not c["is_match"]]
    assert len(mismatches) > 0, "Expected at least one mismatch between conflicting certificates"
    assert mismatches[0]["difference_explanation"] is not None

def test_12_cross_verification_more_than_two_documents(student_user):
    # Upload 3 documents together
    docs = []
    for i, cat in enumerate(["Aadhaar Card", "Income Certificate", "Caste Certificate"]):
        p = create_temp_pdf([
            f"Document Type: {cat}",
            f"Certificate No: CERT-2026-300{i}",
            "Full Name: Ananya Verma",
            "Date of Birth: 24/01/2001"
        ], f"multi_3_{i}.pdf")
        with open(p, "rb") as f:
            u = client.post(
                "/api/documents/upload",
                headers=student_user["headers"],
                files=[("files", (f"multi_3_{i}.pdf", f, "application/pdf"))],
                data={"category": cat}
            )
        docs.append(u.json()[0]["id"])

    cross_res = client.post("/api/verify/multiple", headers=student_user["headers"], json={"document_ids": docs})
    assert cross_res.status_code == 201
    assert len(cross_res.json()["cross_comparisons"]) >= 2

# -------------------------------------------------------------
# 7. RAG Engine Retrieval & Grounding
# -------------------------------------------------------------
def test_13_rag_retrieval_and_explanation():
    rules = rag_engine.retrieve(query="Missing income certificate annual amount in INR", category="Income Certificate", top_k=2)
    assert len(rules) > 0
    assert any("Income" in r.get("category", "") or "General" in r.get("category", "") for r in rules)

    explanation = rag_engine.generate_explanation(
        issue_title="Missing Annual Family Income",
        category="Missing Information",
        expected_val="Positive numeric amount in INR",
        actual_val=None
    )
    assert explanation is not None
    assert len(explanation.get("explanation", "")) > 15
    assert "rag_rule_id" in explanation

# -------------------------------------------------------------
# 8. ReportLab PDF Generation
# -------------------------------------------------------------
def test_14_pdf_report_generation_and_download(student_user):
    # Upload and verify document
    doc_path = create_temp_pdf([
        "Document Type: Caste Certificate",
        "Certificate No: CERT-2026-REPORT",
        "Full Name: Ananya Verma",
        "Caste Category: SC"
    ], "doc_for_report.pdf")
    with open(doc_path, "rb") as f:
        u = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("doc_for_report.pdf", f, "application/pdf"))],
            data={"category": "Caste Certificate"}
        )
    doc_id = u.json()[0]["id"]
    v_res = client.post(f"/api/verify/document/{doc_id}", headers=student_user["headers"])
    v_id = v_res.json()["id"]

    # Generate PDF Report
    gen_res = client.post(f"/api/reports/generate/{v_id}", headers=student_user["headers"])
    assert gen_res.status_code == 201
    report_info = gen_res.json()
    assert "report_id" in report_info
    assert "download_url" in report_info

    # Download PDF and verify binary magic header
    dl_res = client.get(report_info["download_url"], headers=student_user["headers"])
    assert dl_res.status_code == 200
    assert dl_res.content.startswith(b"%PDF"), "Generated report must have valid PDF header"

# -------------------------------------------------------------
# 9. Admin Issue Review and Rules Management
# -------------------------------------------------------------
def test_15_admin_review_and_rule_management(admin_user):
    # 1. List reviews queue
    reviews_res = client.get("/api/admin/reviews", headers=admin_user)
    assert reviews_res.status_code == 200

    # 2. List verification rules
    rules_res = client.get("/api/admin/rules", headers=admin_user)
    assert rules_res.status_code == 200
    rules = rules_res.json()
    assert len(rules) >= 10, "Expected at least 10 seeded verification rules"

    # 3. Update verification rule threshold/validity
    rule_id = rules[0]["id"]
    orig_validity = rules[0].get("validity_period_months", 0)
    update_res = client.put(
        f"/api/admin/rules/{rule_id}",
        headers=admin_user,
        json={"validity_period_months": 36, "is_active": True}
    )
    assert update_res.status_code == 200
    assert update_res.json()["rule_id"] == rule_id

    # Reset rule back
    client.put(
        f"/api/admin/rules/{rule_id}",
        headers=admin_user,
        json={"validity_period_months": orig_validity, "is_active": True}
    )

# -------------------------------------------------------------
# 10. Admin Reference Knowledge Base Management & Semantic Query Testing
# -------------------------------------------------------------
def test_16_admin_knowledge_base_management_and_rag_test_query(admin_user):
    # 1. Fetch reference knowledge base rules
    kb_res = client.get("/api/admin/knowledge-base", headers=admin_user)
    assert kb_res.status_code == 200
    kb_data = kb_res.json()
    assert kb_data["total_rules"] >= 11, "Knowledge base must have at least 11 regulatory rules"
    assert len(kb_data["rules"]) >= 11

    # 2. Test semantic retrieval query
    query_payload = {
        "query": "Income certificate issued over 18 months ago, is it acceptable?",
        "category": "Income Certificate",
        "top_k": 2
    }
    test_res = client.post("/api/admin/knowledge-base/test-query", headers=admin_user, json=query_payload)
    assert test_res.status_code == 200
    test_data = test_res.json()
    assert len(test_data["retrieved_rules"]) > 0
    top_hit = test_data["retrieved_rules"][0]
    assert top_hit["rule_id"] == "KB-RULE-002" or "Income" in top_hit["category"]
    assert "rag_preview" in test_data
    assert "explanation" in test_data["rag_preview"]

    # 3. Add custom knowledge rule
    custom_rule = {
        "id": f"KB-RULE-TEST-{uuid.uuid4().hex[:4]}",
        "category": "Disability Certificate",
        "title": "UDID Card Disability Threshold Benchmark",
        "content": "Eligible applicants must present a Unique Disability ID (UDID) certifying minimum 40% permanent disability.",
        "source": "Rights of Persons with Disabilities Act & Welfare Norms",
        "mandatory_fields": ["udid_number", "disability_percentage"],
        "validity_months": 0
    }
    create_res = client.post("/api/admin/knowledge-base", headers=admin_user, json=custom_rule)
    assert create_res.status_code == 201

    # 4. Update the newly created rule
    update_res = client.put(
        f"/api/admin/knowledge-base/{custom_rule['id']}",
        headers=admin_user,
        json={"title": "UDID Card Disability Threshold Benchmark (Revised 2026)"}
    )
    assert update_res.status_code == 200

    # 5. Delete test rule to keep pristine state
    del_res = client.delete(f"/api/admin/knowledge-base/{custom_rule['id']}", headers=admin_user)
    assert del_res.status_code == 200

# -------------------------------------------------------------
# 11. Evidence Highlighting Viewer API
# -------------------------------------------------------------
def test_17_evidence_highlighting(student_user):
    # Upload a document that will generate an issue (missing required fields)
    doc_path = create_temp_pdf([
        "Document Type: Caste Certificate",
        "Certificate No: CERT-EVIDENCE-001",
        "Issue Date: 12/05/2024"
        # Deliberately missing applicant_name and caste_category
    ], "caste_for_evidence.pdf")
    with open(doc_path, "rb") as f:
        u_res = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("caste_for_evidence.pdf", f, "application/pdf"))],
            data={"category": "Caste Certificate"}
        )
    assert u_res.status_code == 201
    doc_id = u_res.json()[0]["id"]

    v_res = client.post(f"/api/verify/document/{doc_id}", headers=student_user["headers"])
    assert v_res.status_code == 201
    v_data = v_res.json()
    assert len(v_data["issues"]) > 0
    first_issue = v_data["issues"][0]
    issue_id = first_issue["id"]

    # Test GET /api/evidence/{issue_id}
    ev_res = client.get(f"/api/evidence/{issue_id}", headers=student_user["headers"])
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["issue_id"] == issue_id
    assert ev_data["document_id"] == doc_id
    assert "bbox" in ev_data
    assert all(k in ev_data["bbox"] for k in ("x", "y", "width", "height"))
    assert "explanation" in ev_data

    # Test 404 for non-existent issue
    nf_res = client.get("/api/evidence/9999999", headers=student_user["headers"])
    assert nf_res.status_code == 404

# -------------------------------------------------------------
# 12. Application & Document Readiness Scoring API
# -------------------------------------------------------------
def test_18_readiness_scoring(student_user):
    # Test aggregate readiness score across student's documents
    res = client.get("/api/readiness", headers=student_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "application_score" in data
    assert 0 <= data["application_score"] <= 100
    assert "readiness_status" in data
    assert "total_documents" in data
    assert len(data["documents"]) > 0

    # Test specific document readiness score
    doc_id = data["documents"][0]["document_id"]
    doc_res = client.get(f"/api/readiness/{doc_id}", headers=student_user["headers"])
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert doc_data["document_id"] == doc_id
    assert "breakdown" in doc_data
    assert "completeness_score" in doc_data["breakdown"]
    assert "validation_score" in doc_data["breakdown"]
    assert "quality_score" in doc_data["breakdown"]
    assert "deductions" in doc_data

    # Test 404 for non-existent document
    doc_nf = client.get("/api/readiness/999999", headers=student_user["headers"])
    assert doc_nf.status_code == 404

# -------------------------------------------------------------
# 13. Ask Your Document AI Assistant API
# -------------------------------------------------------------
def test_19_assistant_chat(student_user):
    # Post query to assistant
    payload = {"message": "What issues were detected in my uploaded documents and how do I fix them?"}
    chat_res = client.post("/api/assistant/chat", headers=student_user["headers"], json=payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "message" in chat_data
    assert len(chat_data["message"]) > 20
    assert "evidence_references" in chat_data
    assert "model_name" in chat_data

    # Get conversation history
    hist_res = client.get("/api/assistant/history", headers=student_user["headers"])
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert "conversation_id" in hist_data
    assert len(hist_data["messages"]) >= 2
    assert any(m["sender"] == "user" for m in hist_data["messages"])
    assert any(m["sender"] == "assistant" for m in hist_data["messages"])

# -------------------------------------------------------------
# 14. Scholarship Application Readiness Checklist API
# -------------------------------------------------------------
def test_20_checklist_and_schemes(student_user):
    res = client.get("/api/checklist", headers=student_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "available_schemes" in data
    assert len(data["available_schemes"]) >= 1
    assert "selected_scheme" in data
    assert "progress_percentage" in data
    assert "checklist" in data
    assert len(data["checklist"]) > 0

    first_item = data["checklist"][0]
    assert "category" in first_item
    assert "is_uploaded" in first_item
    assert "status" in first_item

# -------------------------------------------------------------
# 15. Document Versioning & Re-Submission API
# -------------------------------------------------------------
def test_21_document_versioning(student_user):
    # Create initial document version 1
    doc_path = create_temp_pdf([
        "Document Type: Study Certificate",
        "Certificate No: CERT-VER-001",
        "Student Name: Ananya Verma",
        "Institution Name: University College of Engineering"
    ], "versioning_test_v1.pdf")
    with open(doc_path, "rb") as f:
        u_res = client.post(
            "/api/documents/upload",
            headers=student_user["headers"],
            files=[("files", ("versioning_test_v1.pdf", f, "application/pdf"))],
            data={"category": "Study Certificate"}
        )
    assert u_res.status_code == 201
    doc_id = u_res.json()[0]["id"]

    # Retrieve initial version history
    v1_res = client.get(f"/api/documents/{doc_id}/versions", headers=student_user["headers"])
    assert v1_res.status_code == 200
    v1_data = v1_res.json()
    assert v1_data["current_version"] == 1
    assert v1_data["total_versions"] == 1

    # Upload corrected revision (version 2)
    doc_path_v2 = create_temp_pdf([
        "Document Type: Study Certificate",
        "Certificate No: CERT-VER-001",
        "Student Name: Ananya Verma",
        "Institution Name: University College of Engineering",
        "Academic Year: 2025-2026",
        "Roll Number: 2026-ROLL-9988",
        "Endorsement: Verified by Principal"
    ], "versioning_test_v2.pdf")
    with open(doc_path_v2, "rb") as f:
        up_res = client.post(
            f"/api/documents/{doc_id}/versions",
            headers=student_user["headers"],
            files=[("file", ("versioning_test_v2.pdf", f, "application/pdf"))],
            data={"change_summary": "Added principal endorsement and academic year"}
        )
    assert up_res.status_code == 201
    assert up_res.json()["new_version"] == 2

    # Verify updated version list
    v2_res = client.get(f"/api/documents/{doc_id}/versions", headers=student_user["headers"])
    assert v2_res.status_code == 200
    v2_data = v2_res.json()
    assert v2_data["current_version"] == 2
    assert v2_data["total_versions"] == 2

# -------------------------------------------------------------
# 16. Pre-Submission Correction Checklist PDF Generation API
# -------------------------------------------------------------
def test_22_correction_checklist_pdf(student_user):
    res = client.post("/api/reports/correction-checklist", headers=student_user["headers"])
    assert res.status_code == 201
    data = res.json()
    assert "report_id" in data
    assert "download_url" in data

    # Download checklist PDF and verify header
    dl_res = client.get(data["download_url"], headers=student_user["headers"])
    assert dl_res.status_code == 200
    assert dl_res.content.startswith(b"%PDF"), "Checklist report must be valid PDF"

# -------------------------------------------------------------
# 17. Admin Audit Trail API & Access Control
# -------------------------------------------------------------
def test_23_admin_audit_logs(student_user, admin_user):
    # Student cannot access administrative audit logs
    forbidden_res = client.get("/api/admin/audit-logs", headers=student_user["headers"])
    assert forbidden_res.status_code == 403

    # Seed an administrative audit event by creating a reference material
    mat_payload = {
        "title": f"Audit Verification Regulation {uuid.uuid4().hex[:4]}",
        "category": "Income Certificate",
        "content": "Official circular on annual income slab verification.",
        "source": "State Revenue Department Directive",
        "authority": "Director of Social Welfare"
    }
    client.post("/api/admin/reference-materials", headers=admin_user, json=mat_payload)

    # Admin can access audit logs
    admin_res = client.get("/api/admin/audit-logs", headers=admin_user)
    assert admin_res.status_code == 200
    logs = admin_res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    first_log = logs[0]
    assert "action" in first_log
    assert "details" in first_log
    assert "timestamp" in first_log

