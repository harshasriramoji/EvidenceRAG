import re
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.entities import Document, ExtractedField, VerificationResult, Issue, VerificationRule
from backend.app.services.rag.engine import rag_engine
from backend.app.services.ocr.extractor import parse_date_string

class SingleDocumentVerifier:
    """
    Implements Mode A: Single Document Verification.
    Examines an individual document for compliance, completeness, validity, quality, and formatting.
    Grounds all detected issues in retrieved RAG rules.
    """

    @staticmethod
    def verify_document(document: Document, db: Session) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []
        raw_text = document.raw_text or ""
        category = document.category
        
        # Load extracted fields as a key-value dictionary
        fields = {ef.field_name: ef.field_value for ef in document.extracted_fields if ef.field_value}

        # 1. OCR Readability & Text Completeness
        if len(raw_text.strip()) < 25 or len(raw_text.split()) < 5:
            issue_info = rag_engine.generate_explanation(
                issue_title="Unreadable OCR Output / Blank Document",
                category=category,
                evidence="Extracted text is empty or fewer than 5 words.",
                expected_val="Legible document text with clear characters",
                actual_val=f"Only {len(raw_text.split())} words extracted"
            )
            issues.append({
                "title": "Unreadable OCR Output",
                "category": "ocr_uncertainty",
                "severity": "critical",
                "document_name": document.original_filename,
                "page_number": 1,
                "evidence_snippet": raw_text[:100] if raw_text else "[No text detected]",
                "expected_value": "Legible certificate content",
                "actual_value": f"{len(raw_text.strip())} characters",
                "explanation": issue_info["explanation"],
                "suggested_correction": issue_info["suggested_correction"],
                "confidence_score": 0.95,
                "manual_review_recommended": True,
                "rag_rule_id": issue_info["rag_rule_id"],
                "rag_source": issue_info["rag_source"]
            })

        # 2. Document Category Mismatch Detection
        category_mismatch = SingleDocumentVerifier._check_category_mismatch(raw_text, category)
        if category_mismatch:
            issue_info = rag_engine.generate_explanation(
                issue_title="Incorrect Document Category Selected",
                category=category,
                evidence=category_mismatch["evidence"],
                expected_val=category,
                actual_val=category_mismatch["detected_category"]
            )
            issues.append({
                "title": "Document Category Mismatch",
                "category": "category_mismatch",
                "severity": "critical",
                "document_name": document.original_filename,
                "page_number": 1,
                "evidence_snippet": category_mismatch["evidence"],
                "expected_value": category,
                "actual_value": category_mismatch["detected_category"],
                "explanation": issue_info["explanation"],
                "suggested_correction": issue_info["suggested_correction"],
                "confidence_score": 0.92,
                "manual_review_recommended": True,
                "rag_rule_id": issue_info["rag_rule_id"],
                "rag_source": issue_info["rag_source"]
            })

        # 3. Mandatory Fields Verification
        rule = db.query(VerificationRule).filter(VerificationRule.document_category == category).first()
        mandatory_field_names = []
        if rule and rule.mandatory_fields:
            try:
                import json
                mandatory_field_names = json.loads(rule.mandatory_fields)
            except Exception:
                pass

        FIELD_ALIASES = {
            "applicant_name": ["applicant_name", "full_name", "student_name", "candidate_name", "account_holder_name"],
            "student_name": ["student_name", "full_name", "applicant_name", "candidate_name"],
            "account_holder_name": ["account_holder_name", "full_name", "applicant_name"],
            "certificate_number": ["certificate_number", "cert_no"],
            "annual_income": ["annual_income", "income"],
            "roll_number": ["roll_number", "hall_ticket_number", "admission_number"],
            "hall_ticket_number": ["hall_ticket_number", "roll_number"],
            "course_name": ["course_name", "course"],
            "account_number": ["account_number", "bank_acc"],
            "total_marks_or_grade": ["total_marks_or_grade", "marks", "cgpa"],
            "exam_month_year": ["exam_month_year", "issue_date"],
            "branch_name": ["branch_name", "address"]
        }

        for field_req in mandatory_field_names:
            aliases = FIELD_ALIASES.get(field_req, [field_req])
            found_val = any(fields.get(a) for a in aliases)
            if not found_val:
                field_display = field_req.replace("_", " ").title()
                issue_info = rag_engine.generate_explanation(
                    issue_title=f"Missing Mandatory Field: {field_display}",
                    category=category,
                    evidence=f"Field '{field_req}' not found in OCR extraction",
                    expected_val=field_display,
                    actual_val="Missing / Not Found"
                )
                issues.append({
                    "title": f"Missing Mandatory Field: {field_display}",
                    "category": "missing_field",
                    "severity": "critical" if field_req in ("full_name", "applicant_name", "student_name") else "high",
                    "document_name": document.original_filename,
                    "page_number": 1,
                    "evidence_snippet": f"Document text missing {field_display} identifier.",
                    "expected_value": f"Valid {field_display}",
                    "actual_value": "null",
                    "explanation": issue_info["explanation"],
                    "suggested_correction": issue_info["suggested_correction"],
                    "confidence_score": 0.90,
                    "manual_review_recommended": False,
                    "rag_rule_id": issue_info["rag_rule_id"],
                    "rag_source": issue_info["rag_source"]
                })

        # 4. Name Quality & Spelling Checks
        extracted_name = fields.get("full_name")
        if extracted_name:
            if len(extracted_name.strip()) < 3:
                issues.append(SingleDocumentVerifier._build_issue(
                    title="Incomplete Name Field",
                    category="possible_inconsistencies",
                    severity="high",
                    doc_name=document.original_filename,
                    evidence=extracted_name,
                    expected="Full legal name (minimum 3 characters)",
                    actual=extracted_name,
                    rag_category=category
                ))
            elif re.search(r"\d", extracted_name):
                issues.append(SingleDocumentVerifier._build_issue(
                    title="Numeric Characters in Name Field",
                    category="confirmed_error",
                    severity="high",
                    doc_name=document.original_filename,
                    evidence=extracted_name,
                    expected="Alphabetic legal name",
                    actual=extracted_name,
                    rag_category=category
                ))

        # 5. Date Validity, Impossible Dates & Format Checks
        # Check DOB
        dob_val = fields.get("dob")
        if dob_val:
            dob_date = parse_date_string(dob_val)
            if not dob_date:
                issues.append(SingleDocumentVerifier._build_issue(
                    title="Invalid Date of Birth Format",
                    category="invalid_date",
                    severity="high",
                    doc_name=document.original_filename,
                    evidence=dob_val,
                    expected="DD/MM/YYYY or YYYY-MM-DD",
                    actual=dob_val,
                    rag_category=category
                ))
            else:
                today = datetime.date.today()
                if dob_date > today:
                    issues.append(SingleDocumentVerifier._build_issue(
                        title="Impossible Future Date of Birth",
                        category="confirmed_error",
                        severity="critical",
                        doc_name=document.original_filename,
                        evidence=f"DOB: {dob_val}",
                        expected=f"Date prior to {today.strftime('%d/%m/%Y')}",
                        actual=dob_val,
                        rag_category=category
                    ))
                elif (today.year - dob_date.year) > 90 or (today.year - dob_date.year) < 3:
                    issues.append(SingleDocumentVerifier._build_issue(
                        title="Unusual Age in Date of Birth",
                        category="manual_review_recommendation",
                        severity="medium",
                        doc_name=document.original_filename,
                        evidence=f"Age computed: {today.year - dob_date.year} years",
                        expected="Plausible student applicant age (14-40 years)",
                        actual=f"{today.year - dob_date.year} years",
                        rag_category=category,
                        manual_review=True
                    ))

        # Check Issue Date
        issue_date_val = fields.get("issue_date")
        if issue_date_val:
            issue_date = parse_date_string(issue_date_val)
            if not issue_date:
                issues.append(SingleDocumentVerifier._build_issue(
                    title="Invalid Issue Date Format",
                    category="invalid_date",
                    severity="medium",
                    doc_name=document.original_filename,
                    evidence=issue_date_val,
                    expected="DD/MM/YYYY format",
                    actual=issue_date_val,
                    rag_category=category
                ))
            else:
                # 6. Expiry Detection based on configured validity rules
                validity_months = rule.validity_period_months if rule else 0
                if validity_months > 0:
                    today = datetime.date.today()
                    # Calculate difference in days (~30 days per month)
                    days_valid = validity_months * 30.5
                    elapsed_days = (today - issue_date).days
                    if elapsed_days > days_valid:
                        issues.append(SingleDocumentVerifier._build_issue(
                            title=f"Expired Certificate ({validity_months} Months Validity)",
                            category="confirmed_error",
                            severity="critical",
                            doc_name=document.original_filename,
                            evidence=f"Issue Date: {issue_date_val} (Issued {elapsed_days} days ago)",
                            expected=f"Issued within the past {validity_months} months",
                            actual=f"Issued {elapsed_days} days ago (Exceeded {int(days_valid)} days limit)",
                            rag_category=category
                        ))

        # 7. Identifier Format Validation (Aadhaar, IFSC)
        if category == "Aadhaar Card":
            aadhaar_val = fields.get("aadhaar_number")
            if aadhaar_val:
                clean_aadhaar = re.sub(r"\s+", "", aadhaar_val)
                if len(clean_aadhaar) != 12 or not clean_aadhaar.isdigit():
                    issues.append(SingleDocumentVerifier._build_issue(
                        title="Invalid Aadhaar Number Format",
                        category="confirmed_error",
                        severity="high",
                        doc_name=document.original_filename,
                        evidence=aadhaar_val,
                        expected="12-digit numeric UID (e.g. 1234 5678 9012)",
                        actual=aadhaar_val,
                        rag_category=category
                    ))

        if category == "Bank Passbook":
            ifsc_val = fields.get("ifsc_code")
            if ifsc_val:
                if len(ifsc_val) != 11 or ifsc_val[4] != "0":
                    issues.append(SingleDocumentVerifier._build_issue(
                        title="Invalid Bank IFSC Code Format",
                        category="confirmed_error",
                        severity="high",
                        doc_name=document.original_filename,
                        evidence=ifsc_val,
                        expected="11-character alphanumeric IFSC with 5th character '0'",
                        actual=ifsc_val,
                        rag_category=category
                    ))

        # 8. Visual & Scan Quality Issues
        if document.is_blurry or document.image_quality_score < 0.65:
            issues.append(SingleDocumentVerifier._build_issue(
                title="Blurry Document Scan Detected",
                category="poor_image_quality",
                severity="high",
                doc_name=document.original_filename,
                evidence=f"Quality score: {document.image_quality_score}, Blur flag: {document.is_blurry}",
                expected="Sharp, high-contrast scan with Laplacian variance > 95",
                actual="High optical blur detected",
                rag_category="General Quality",
                manual_review=True
            ))

        if document.is_low_res:
            issues.append(SingleDocumentVerifier._build_issue(
                title="Low Resolution Scan",
                category="poor_image_quality",
                severity="medium",
                doc_name=document.original_filename,
                evidence="Image dimensions below 650x650 pixels",
                expected="Minimum scan resolution of 150-300 DPI (>= 700x700px)",
                actual="Low pixel count scan",
                rag_category="General Quality"
            ))

        if document.is_rotated:
            issues.append(SingleDocumentVerifier._build_issue(
                title="Rotated / Misaligned Document",
                category="suspicious_indicators",
                severity="medium",
                doc_name=document.original_filename,
                evidence="Hough line analysis indicates vertical text orientation",
                expected="Upright portrait orientation (0 degrees)",
                actual="Rotated document orientation",
                rag_category="General Quality"
            ))

        # 9. Signature / Official Stamp Indicator Check
        if category in ("Income Certificate", "Caste Certificate", "Residence Certificate", "Study Certificate", "Bonafide Certificate"):
            has_sig = bool(re.search(r"\b(signature|signed|sign|officer|principal|tahsildar|seal|stamp|dsc|e-sign)\b", raw_text, re.IGNORECASE))
            if not has_sig:
                issues.append(SingleDocumentVerifier._build_issue(
                    title="Missing Signature or Official Seal Indicator",
                    category="manual_review_recommendation",
                    severity="medium",
                    doc_name=document.original_filename,
                    evidence="No signature, seal, or digital attestation keyword detected in document text.",
                    expected="Issuing authority signature, departmental seal, or digital DSC endorsement",
                    actual="No endorsement indicators identified",
                    rag_category="Authentication Endorsement",
                    manual_review=True
                ))

        # 10. Compute Overall Status
        critical_count = sum(1 for i in issues if i["severity"] == "critical")
        high_count = sum(1 for i in issues if i["severity"] == "high")
        warning_count = sum(1 for i in issues if i["severity"] in ("high", "medium", "low"))
        manual_review_needed = any(i.get("manual_review_recommended", False) for i in issues)

        if critical_count > 0:
            overall_status = "Needs Correction"
        elif manual_review_needed or high_count > 0:
            overall_status = "Manual Review Required"
        elif warning_count > 0:
            overall_status = "Passed with Warnings"
        else:
            overall_status = "Passed"

        return {
            "overall_status": overall_status,
            "total_issues": len(issues),
            "critical_issues": critical_count,
            "warning_issues": warning_count,
            "issues": issues,
            "summary": f"Verification completed with status '{overall_status}'. Identified {critical_count} critical issues and {warning_count} warnings/recommendations."
        }

    @staticmethod
    def _build_issue(
        title: str,
        category: str,
        severity: str,
        doc_name: str,
        evidence: str,
        expected: str,
        actual: str,
        rag_category: str,
        manual_review: bool = False
    ) -> Dict[str, Any]:
        info = rag_engine.generate_explanation(
            issue_title=title,
            category=rag_category,
            evidence=evidence,
            expected_val=expected,
            actual_val=actual
        )
        return {
            "title": title,
            "category": category,
            "severity": severity,
            "document_name": doc_name,
            "page_number": 1,
            "evidence_snippet": evidence,
            "expected_value": expected,
            "actual_value": actual,
            "explanation": info["explanation"],
            "suggested_correction": info["suggested_correction"],
            "confidence_score": info.get("confidence", 0.90),
            "manual_review_recommended": manual_review,
            "rag_rule_id": info["rag_rule_id"],
            "rag_source": info["rag_source"]
        }

    @staticmethod
    def _check_category_mismatch(text: str, category: str) -> Optional[Dict[str, str]]:
        t_low = text.lower()
        if category == "Income Certificate":
            if "aadhaar" in t_low or "unique identification" in t_low:
                return {"detected_category": "Aadhaar Card", "evidence": "Document contains 'Unique Identification Authority of India'"}
            if "passbook" in t_low or "account number" in t_low and "ifsc" in t_low:
                return {"detected_category": "Bank Passbook", "evidence": "Document contains Bank account details"}
        elif category == "Aadhaar Card":
            if "income certificate" in t_low or "annual income" in t_low:
                return {"detected_category": "Income Certificate", "evidence": "Document declares annual family income"}
        elif category == "Caste Certificate":
            if "marks memo" in t_low or "hall ticket" in t_low:
                return {"detected_category": "Marks Memo", "evidence": "Document displays subject marks breakdown"}
        return None
