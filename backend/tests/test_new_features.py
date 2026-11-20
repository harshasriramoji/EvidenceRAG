import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.entities import User, Application, Guideline, Notification, SupportTicket, Document

client = TestClient(app)

@pytest.fixture(scope="module")
def student_auth_headers():
    email = f"student_test_{os.getpid()}@example.com"
    pwd = "StudentPassword123!"
    # Register
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "role": "student"
    })
    assert reg_resp.status_code in [201, 200]
    token = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "email": email}

@pytest.fixture(scope="module")
def admin_auth_headers():
    email = f"admin_test_{os.getpid()}@example.com"
    pwd = "AdminPassword123!"
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "role": "admin",
        "admin_code": "AdminSecret@2026"
    })
    assert reg_resp.status_code in [201, 200]
    token = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "email": email}

def test_application_lifecycle(student_auth_headers, admin_auth_headers):
    # 1. Create Application
    create_resp = client.post("/api/applications", headers=student_auth_headers, json={
        "title": "Post-Matric Scholarship 2026",
        "scholarship_name": "National Scholarship Scheme",
        "academic_year": "2025-2026",
        "notes": "Testing application creation"
    })
    assert create_resp.status_code == 201
    app_data = create_resp.json()
    app_id = app_data["id"]
    assert app_data["status"] == "Draft"
    assert "APP-" in app_data["application_number"]

    # 2. List Applications
    list_resp = client.get("/api/applications", headers=student_auth_headers)
    assert list_resp.status_code == 200
    apps = list_resp.json()
    assert any(a["id"] == app_id for a in apps)

    # Attach a document to allow submission
    db = SessionLocal()
    user = db.query(User).filter(User.email == student_auth_headers["email"]).first()
    test_doc = Document(
        user_id=user.id,
        category="Income Certificate",
        filename="Income_Test.pdf",
        original_filename="Income_Test.pdf",
        file_path="uploads/Income_Test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        upload_status="PROCESSED"
    )
    db.add(test_doc)
    db.commit()
    db.refresh(test_doc)
    doc_id = test_doc.id
    db.close()

    attach_resp = client.post(f"/api/applications/{app_id}/attach-document/{doc_id}", headers=student_auth_headers)
    assert attach_resp.status_code == 200

    # 3. Submit Application
    submit_resp = client.post(f"/api/applications/{app_id}/submit", headers=student_auth_headers)
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "Submitted"

def test_guidelines_management(student_auth_headers, admin_auth_headers):
    # 1. List Guidelines as Student
    list_resp = client.get("/api/guidelines", headers=student_auth_headers)
    assert list_resp.status_code == 200
    guidelines = list_resp.json()
    assert len(guidelines) >= 1

    # 2. Admin creates/uploads a new guideline via Form data
    create_resp = client.post("/api/guidelines", headers=admin_auth_headers, data={
        "title": "State Post-Matric Merit Criteria 2026",
        "issuing_authority": "Higher Education Board",
        "category": "Income Certificate",
        "content": "Gross annual family income must not exceed INR 2,50,000 for full fee reimbursement.",
        "version": "1.0",
        "effective_from": "2026-01-01"
    })
    assert create_resp.status_code == 201
    g_id = create_resp.json()["id"]

    # 3. Toggle Status
    toggle_resp = client.put(f"/api/guidelines/{g_id}/status", headers=admin_auth_headers, json={
        "is_active": True,
        "is_approved": True
    })
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_approved"] is True

def test_reviewer_queue_and_decisions(admin_auth_headers):
    # Admin has reviewer rights
    queue_resp = client.get("/api/reviews/queue", headers=admin_auth_headers)
    assert queue_resp.status_code == 200
    data = queue_resp.json()
    assert "total_flagged_issues" in data
    assert "pending_applications" in data
    assert "flagged_issues" in data

def test_notifications_workflow(student_auth_headers):
    db = SessionLocal()
    # Add a mock notification for the student
    user = db.query(User).filter(User.email == student_auth_headers["email"]).first()
    notif = Notification(
        user_id=user.id,
        title="Application Status Updated",
        message="Your scholarship application has been moved to Under Review.",
        category="application",
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    notif_id = notif.id
    db.close()

    # List notifications
    list_resp = client.get("/api/notifications", headers=student_auth_headers)
    assert list_resp.status_code == 200
    resp_data = list_resp.json()
    assert resp_data["unread_count"] >= 1
    assert any(n["id"] == notif_id for n in resp_data["notifications"])

    # Mark single notification as read
    read_resp = client.put(f"/api/notifications/{notif_id}/read", headers=student_auth_headers)
    assert read_resp.status_code == 200

    # Mark all read
    read_all_resp = client.put("/api/notifications/read-all", headers=student_auth_headers)
    assert read_all_resp.status_code == 200

def test_support_ticket_workflow(student_auth_headers, admin_auth_headers):
    # 1. Student creates ticket
    create_resp = client.post("/api/support", headers=student_auth_headers, json={
        "subject": "Income certificate validity query",
        "category": "Verification Question",
        "priority": "High",
        "message": "My income certificate was issued 8 months ago. Is it valid?"
    })
    assert create_resp.status_code == 201
    ticket = create_resp.json()
    ticket_id = ticket["id"]
    assert ticket["status"] == "Open"
    assert "TKT-" in ticket["ticket_number"]

    # 2. Student lists tickets
    my_tickets = client.get("/api/support", headers=student_auth_headers).json()
    assert any(t["id"] == ticket_id for t in my_tickets)

    # 3. Admin replies to ticket
    reply_resp = client.put(f"/api/support/{ticket_id}/reply", headers=admin_auth_headers, json={
        "admin_reply": "Income certificates issued within 12 months are accepted under current guidelines.",
        "status": "Resolved"
    })
    assert reply_resp.status_code == 200
    assert reply_resp.json()["status"] == "Resolved"
    assert "12 months" in reply_resp.json()["admin_reply"]

def test_faiss_engine_and_gemini_fallback():
    from backend.app.services.rag.faiss_engine import faiss_store
    from backend.app.services.rag.gemini_client import gemini_verifier

    faiss_store.reset()

    texts = [
        "Annual income must not exceed 2.5 LPA according to NSP guidelines.",
        "Aadhaar number must be 12 digits and clearly legible.",
        "Caste certificate must bear the digital signature of the Tahsildar."
    ]
    metadatas = [
        {"rule_id": "KB-RULE-002", "title": "Income Limit", "category": "Income"},
        {"rule_id": "KB-RULE-001", "title": "Aadhaar Standard", "category": "Aadhaar"},
        {"rule_id": "KB-RULE-004", "title": "Caste Authenticity", "category": "Caste"}
    ]
    faiss_store.add_documents(texts, metadatas)

    # Semantic search
    results = faiss_store.search("What is the income ceiling?", top_k=2)
    assert len(results) >= 1
    assert any("2.5 LPA" in r["text"] for r in results)

    # Gemini Verifier with deterministic fallback
    result = gemini_verifier.verify_evidence(
        requirement_title="Annual Family Income Ceiling",
        applicant_evidence="Annual Family Income: INR 3,00,000",
        guideline_content="Gross annual family income from all sources must not exceed INR 2,50,000.",
        expected_value="<= 2,50,000",
        actual_value="3,00,000"
    )
    assert result["finding_status"] in ["Passed", "Flagged", "Needs Review", "Missing Evidence"]
    assert "explanation" in result
    assert "suggested_correction" in result

def test_docx_document_processing():
    import docx
    import tempfile
    from backend.app.services.ocr.processor import process_document_ocr

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        tmp_path = tf.name

    doc = docx.Document()
    doc.add_heading("State Scholarship Bonafide Certificate", level=1)
    doc.add_paragraph("This is to certify that Harsh Vardhan is a regular student.")
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Registration No"
    table.rows[0].cells[1].text = "2024-ENG-0891"
    table.rows[1].cells[0].text = "Annual Family Income"
    table.rows[1].cells[1].text = "INR 1,20,000"
    doc.save(tmp_path)

    try:
        res = process_document_ocr(
            tmp_path,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert "Harsh Vardhan" in res["full_text"]
        assert "2024-ENG-0891" in res["full_text"]
        assert "1,20,000" in res["full_text"]
        assert res["page_count"] >= 1
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
