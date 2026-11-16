import json
import logging
from backend.app.database.session import engine, Base, SessionLocal
from backend.app.models.entities import User, VerificationRule, ScholarshipRequirement, ReferenceMaterial
from backend.app.core.security import get_password_hash
from backend.app.services.rag.knowledge_base import KNOWLEDGE_RULES

logger = logging.getLogger("evidencerag.init_db")

DEFAULT_RULES = [
    {
        "rule_code": "RULE_AADHAAR",
        "document_category": "Aadhaar Card",
        "name": "Aadhaar Identity Verification Rule",
        "description": "Verifies mandatory fields on Aadhaar card: Full name, Date of birth, 12-digit Aadhaar UID format, Gender, and Address.",
        "mandatory_fields": json.dumps(["full_name", "dob", "aadhaar_number", "gender", "address"]),
        "validity_period_months": 0
    },
    {
        "rule_code": "RULE_INCOME",
        "document_category": "Income Certificate",
        "name": "Income Certificate Validity & Mandatory Fields Rule",
        "description": "Requires applicant name, annual income amount in INR, certificate issue date, and official certificate number. Validity is strictly 12 months from issue date.",
        "mandatory_fields": json.dumps(["applicant_name", "annual_income", "issue_date", "certificate_number"]),
        "validity_period_months": 12
    },
    {
        "rule_code": "RULE_CASTE",
        "document_category": "Caste Certificate",
        "name": "Caste / Community Certificate Rule",
        "description": "Requires applicant name, caste category (e.g. SC/ST/OBC/EWS), certificate number, and issue date.",
        "mandatory_fields": json.dumps(["applicant_name", "caste_category", "certificate_number", "issue_date"]),
        "validity_period_months": 0
    },
    {
        "rule_code": "RULE_RESIDENCE",
        "document_category": "Residence Certificate",
        "name": "Residence / Domicile Certificate Rule",
        "description": "Requires applicant name, full address, certificate number, and issue date. Valid up to 36 months.",
        "mandatory_fields": json.dumps(["applicant_name", "address", "certificate_number", "issue_date"]),
        "validity_period_months": 36
    },
    {
        "rule_code": "RULE_STUDY",
        "document_category": "Study Certificate",
        "name": "Study / Custody Certificate Rule",
        "description": "Requires student name, institution name, academic year, and admission/roll number.",
        "mandatory_fields": json.dumps(["student_name", "institution_name", "academic_year", "roll_number"]),
        "validity_period_months": 12
    },
    {
        "rule_code": "RULE_BONAFIDE",
        "document_category": "Bonafide Certificate",
        "name": "Bonafide Student Certificate Rule",
        "description": "Requires student name, educational institution name, degree/course title, and current academic year.",
        "mandatory_fields": json.dumps(["student_name", "institution_name", "course_name", "academic_year"]),
        "validity_period_months": 12
    },
    {
        "rule_code": "RULE_MARKS_MEMO",
        "document_category": "Marks Memo",
        "name": "Academic Transcript / Marks Memo Rule",
        "description": "Requires student name, hall ticket/roll number, institution/board name, total marks/CGPA, and exam month/year.",
        "mandatory_fields": json.dumps(["student_name", "hall_ticket_number", "institution_name", "total_marks_or_grade", "exam_month_year"]),
        "validity_period_months": 0
    },
    {
        "rule_code": "RULE_BANK_PASSBOOK",
        "document_category": "Bank Passbook",
        "name": "Bank Passbook Account Verification Rule",
        "description": "Requires account holder name matching applicant, valid bank account number, 11-character IFSC code, bank name, and branch.",
        "mandatory_fields": json.dumps(["account_holder_name", "account_number", "ifsc_code", "bank_name", "branch_name"]),
        "validity_period_months": 0
    },
    {
        "rule_code": "RULE_PHOTO",
        "document_category": "Passport-size Photograph",
        "name": "Passport Photo Specification Rule",
        "description": "Requires recent passport-size photograph with clear contrast, proper orientation, not blurry, and taken within the past 6 months.",
        "mandatory_fields": json.dumps(["face_detected"]),
        "validity_period_months": 6
    },
    {
        "rule_code": "RULE_OTHER",
        "document_category": "Other Supporting Documents",
        "name": "General Supporting Document Rule",
        "description": "Requires readable content, legitimate issuing authority indicator, and documented title.",
        "mandatory_fields": json.dumps(["document_title"]),
        "validity_period_months": 0
    }
]

def init_database():
    """Create tables and seed initial verification rules."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Perform lightweight schema migration for existing SQLite files
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            for table, col, col_type in [
                ("verification_results", "readiness_score", "INTEGER DEFAULT 100"),
                ("issues", "bbox_x", "FLOAT"),
                ("issues", "bbox_y", "FLOAT"),
                ("issues", "bbox_width", "FLOAT"),
                ("issues", "bbox_height", "FLOAT"),
                ("documents", "version", "INTEGER DEFAULT 1"),
                ("documents", "language", "VARCHAR DEFAULT 'eng'"),
                ("extracted_fields", "bbox_x", "FLOAT"),
                ("extracted_fields", "bbox_y", "FLOAT"),
                ("extracted_fields", "bbox_width", "FLOAT"),
                ("extracted_fields", "bbox_height", "FLOAT"),
                ("admin_reviews", "previous_status", "VARCHAR"),
                ("admin_reviews", "new_status", "VARCHAR"),
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    conn.commit()
                except Exception:
                    # Column already exists
                    pass
    except Exception as e:
        logger.warning(f"Schema column check: {e}")

    db = SessionLocal()
    try:
        # Seed Verification Rules (Administrative Reference Knowledge)
        for r_data in DEFAULT_RULES:
            existing = db.query(VerificationRule).filter(VerificationRule.rule_code == r_data["rule_code"]).first()
            if not existing:
                logger.info(f"Seeding rule: {r_data['rule_code']}")
                rule = VerificationRule(
                    rule_code=r_data["rule_code"],
                    document_category=r_data["document_category"],
                    name=r_data["name"],
                    description=r_data["description"],
                    mandatory_fields=r_data["mandatory_fields"],
                    validity_period_months=r_data["validity_period_months"],
                    is_active=True
                )
                db.add(rule)

        # Seed default administrator if not present
        admin_email = "admin@evidencerag.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                full_name="System Administrator",
                hashed_password=get_password_hash("Admin@12345"),
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            logger.info("Default administrator seeded: admin@evidencerag.com")

        # Seed Default Scholarship Schemes for Checklist
        DEFAULT_SCHEMES = [
            {
                "scholarship_name": "Post-Matric Scholarship Scheme (PMS)",
                "description": "Standard state & central post-matric higher education financial grant for eligible applicants.",
                "required_categories": json.dumps([
                    "Aadhaar Card",
                    "Income Certificate",
                    "Caste Certificate",
                    "Residence Certificate",
                    "Bonafide Certificate",
                    "Bank Passbook"
                ]),
                "min_readiness_score": 80
            },
            {
                "scholarship_name": "National Merit-cum-Means Scholarship (NMMS)",
                "description": "Merit-focused grant requiring high academic transcripts and income threshold compliance.",
                "required_categories": json.dumps([
                    "Aadhaar Card",
                    "Income Certificate",
                    "Marks Memo",
                    "Study Certificate",
                    "Bank Passbook"
                ]),
                "min_readiness_score": 85
            },
            {
                "scholarship_name": "Central Sector University & College Scholarship",
                "description": "Ministry of Education scheme for top percentile university graduates.",
                "required_categories": json.dumps([
                    "Aadhaar Card",
                    "Income Certificate",
                    "Marks Memo",
                    "Bonafide Certificate",
                    "Bank Passbook"
                ]),
                "min_readiness_score": 80
            }
        ]

        for scheme_data in DEFAULT_SCHEMES:
            existing_s = db.query(ScholarshipRequirement).filter(
                ScholarshipRequirement.scholarship_name == scheme_data["scholarship_name"]
            ).first()
            if not existing_s:
                scheme = ScholarshipRequirement(
                    scholarship_name=scheme_data["scholarship_name"],
                    description=scheme_data["description"],
                    required_categories=scheme_data["required_categories"],
                    min_readiness_score=scheme_data["min_readiness_score"],
                    is_active=True
                )
                db.add(scheme)

        # Seed Reference Materials from KNOWLEDGE_RULES
        for kb_item in KNOWLEDGE_RULES:
            existing_rm = db.query(ReferenceMaterial).filter(
                ReferenceMaterial.title == kb_item["title"]
            ).first()
            if not existing_rm:
                rm = ReferenceMaterial(
                    title=kb_item["title"],
                    category=kb_item["category"],
                    content=kb_item["content"],
                    source=kb_item["source"],
                    authority="State & Central Government Portals",
                    is_active=True
                )
                db.add(rm)

        db.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
