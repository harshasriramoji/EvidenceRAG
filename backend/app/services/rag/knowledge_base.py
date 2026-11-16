"""
Knowledge Base of Document Verification Guidelines and Regulatory Rules for EvidenceRAG
"""

from typing import List, Dict, Any

KNOWLEDGE_RULES: List[Dict[str, Any]] = [
    {
        "id": "KB-RULE-001",
        "category": "Aadhaar Card",
        "title": "Aadhaar Mandatory Identification Specifications",
        "content": (
            "Aadhaar cards submitted for scholarship identity verification must contain the applicant's full legal name, "
            "date of birth (DOB) in DD/MM/YYYY or YYYY format, 12-digit Unique Identification Number (UID) properly formatted "
            "as XXXX XXXX XXXX, gender, and residential address. Documents with blurred UID numbers or missing DOB will be rejected. "
            "Aadhaar is a permanent identity document with no expiration date."
        ),
        "source": "UIDAI Identity Verification Circular & National Scholarship Portal (NSP) Section 3.1",
        "mandatory_fields": ["full_name", "dob", "aadhaar_number", "gender", "address"],
        "validity_months": 0
    },
    {
        "id": "KB-RULE-002",
        "category": "Income Certificate",
        "title": "Income Certificate Validity & Annual Income Thresholds",
        "content": (
            "An Income Certificate is mandatory to establish financial eligibility for government scholarship schemes. "
            "The certificate must explicitly state the candidate's legal name, annual family income in Indian Rupees (both figures and words), "
            "official certificate number issued by the competent revenue authority (Tahsildar/Mandal Revenue Officer), and issue date. "
            "Under state and central scholarship rules, an income certificate is valid for exactly one year (12 months) from its date of issuance. "
            "Any income certificate issued more than 12 months prior to the application deadline is deemed expired."
        ),
        "source": "State Revenue Department Guidelines & Post-Matric Scholarship Policy, Section 4.2",
        "mandatory_fields": ["applicant_name", "annual_income", "issue_date", "certificate_number"],
        "validity_months": 12
    },
    {
        "id": "KB-RULE-003",
        "category": "Caste Certificate",
        "title": "Community / Caste Certificate Requirements",
        "content": (
            "Caste / Community certificates submitted for reserved category scholarships (SC/ST/OBC/EWS) must state the applicant's "
            "full name, father's/mother's name, recognized sub-caste, official community code, issuing revenue officer signature, "
            "and government emblem/seal. Permanent caste certificates do not expire unless issued under an annual income-linked "
            "creamy layer quota (OBC Non-Creamy Layer / EWS) which requires financial re-certification."
        ),
        "source": "Ministry of Social Justice & Empowerment Caste Verification Guidelines",
        "mandatory_fields": ["applicant_name", "caste_category", "certificate_number", "issue_date"],
        "validity_months": 0
    },
    {
        "id": "KB-RULE-004",
        "category": "Residence Certificate",
        "title": "Residence and Domicile Certificate Criteria",
        "content": (
            "Residence/Domicile certificates prove regional eligibility for domicile-restricted scholarship allocations. "
            "The document must indicate the applicant's complete residential address including door/flat number, street, "
            "locality, town/village, district, state, and 6-digit postal PIN code. A residence certificate remains valid for up to "
            "36 months (3 years) from issue date."
        ),
        "source": "State Higher Education Directorate Domicile Norms, Clause 8",
        "mandatory_fields": ["applicant_name", "address", "certificate_number", "issue_date"],
        "validity_months": 36
    },
    {
        "id": "KB-RULE-005",
        "category": "Study Certificate",
        "title": "Study Certificate Academic Verification",
        "content": (
            "Study certificates certify that the student is genuinely enrolled in a recognized institution for the current academic year. "
            "The document must contain the student's name, admission or roll number, institutional affiliation/code, current course/branch, "
            "and academic session (e.g. 2024-2025). The certificate must bear the signature and seal of the Head of the Institution or Principal."
        ),
        "source": "University Grants Commission (UGC) & State Board Academic Verification Norms",
        "mandatory_fields": ["student_name", "institution_name", "academic_year", "roll_number"],
        "validity_months": 12
    },
    {
        "id": "KB-RULE-006",
        "category": "Bonafide Certificate",
        "title": "Bonafide Student Certification Rules",
        "content": (
            "A bonafide certificate attests to the applicant's continuous good standing as a regular full-time student. "
            "It must specify the student's full name matching their admission register, current course of study, semester/year, "
            "and date of issue. Bonafide certificates are valid only for the academic year in which they were issued."
        ),
        "source": "Institutional Scholarship Compliance Handbook, Rule 11.4",
        "mandatory_fields": ["student_name", "institution_name", "course_name", "academic_year"],
        "validity_months": 12
    },
    {
        "id": "KB-RULE-007",
        "category": "Marks Memo",
        "title": "Academic Marks Memo & Grade Transcript Validation",
        "content": (
            "Marks memos or grade sheets verify academic merit thresholds (e.g. minimum 60% or equivalent CGPA). "
            "The document must display the candidate's name, hall ticket/registration number, examination month and year, "
            "breakdown of subjects, total marks or CGPA awarded, and result declaration status (Pass/First Class). "
            "Scans with cut off grade tables or missing total percentages require manual re-upload."
        ),
        "source": "National Merit Scholarship Evaluation Framework, Section 5",
        "mandatory_fields": ["student_name", "hall_ticket_number", "institution_name", "total_marks_or_grade", "exam_month_year"],
        "validity_months": 0
    },
    {
        "id": "KB-RULE-008",
        "category": "Bank Passbook",
        "title": "Direct Benefit Transfer (DBT) Bank Account Passbook",
        "content": (
            "Scholarship disbursement via Direct Benefit Transfer (DBT) requires an active bank account in the sole name of the student. "
            "The front page scan of the bank passbook or cancelled cheque must show: Account Holder Name (strictly matching student ID), "
            "Bank Account Number (9 to 18 digits), Bank Name and Branch, and valid 11-character Indian Financial System Code (IFSC). "
            "Joint accounts or accounts missing branch IFSC codes cannot be verified."
        ),
        "source": "Public Financial Management System (PFMS) & Reserve Bank of India DBT Directives",
        "mandatory_fields": ["account_holder_name", "account_number", "ifsc_code", "bank_name", "branch_name"],
        "validity_months": 0
    },
    {
        "id": "KB-RULE-009",
        "category": "General Quality",
        "title": "Digital Document Quality and Scan Standards",
        "content": (
            "All uploaded application documents must be legible, unblurred, and scanned at an effective resolution of at least 150-300 DPI. "
            "Images with Laplacian variance under 95.0 are classified as blurry and risk OCR extraction failures. "
            "Documents rotated by 90 or 180 degrees, cropped borders hiding text margins, or blank/damaged pages must be re-scanned "
            "prior to final scholarship submission."
        ),
        "source": "Digital India Document Ingestion Standards & ISO 12653 Electronic Document Quality",
        "mandatory_fields": [],
        "validity_months": 0
    },
    {
        "id": "KB-RULE-010",
        "category": "Date Validity",
        "title": "Date Integrity and Logical Chronology",
        "content": (
            "All dates on uploaded credentials must be chronologically sound. Dates of birth cannot be in the future or exceed plausible student ages. "
            "Certificate issue dates cannot precede the applicant's birth date or succeed the current date. "
            "Dates must follow standard recognized formats (DD/MM/YYYY, YYYY-MM-DD). Non-existent calendar dates (e.g. February 31) are invalid."
        ),
        "source": "National Portal Application Validation Standard, Rule 2.4",
        "mandatory_fields": ["issue_date"],
        "validity_months": 0
    },
    {
        "id": "KB-RULE-011",
        "category": "Authentication Endorsement",
        "title": "Signatures, Official Seals and Digital Endorsement",
        "content": (
            "Certificates must carry evidence of authorized issuance. This includes physical signatures with departmental stamps, "
            "or verifiable digital signature certificates (e-Sign, DSC, QR verification code). Documents completely lacking signature "
            "or seal indicators are marked for administrative manual review, but must not be summarily deemed fraudulent without human inspection."
        ),
        "source": "Information Technology Act 2000 & Government e-Governance Authentication Framework",
        "mandatory_fields": [],
        "validity_months": 0
    }
]
