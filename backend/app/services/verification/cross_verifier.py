import re
import difflib
import json
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from backend.app.models.entities import Document, ExtractedField, VerificationResult, Issue, CrossDocumentComparison
from backend.app.services.verification.single_verifier import SingleDocumentVerifier
from backend.app.services.rag.engine import rag_engine
from backend.app.services.ocr.extractor import parse_date_string
from backend.app.core.config import settings

def normalize_text(text: str) -> str:
    """Normalize text: lowercasing, strip honorifics, collapse whitespace."""
    if not text:
        return ""
    t = text.lower()
    # Strip common honorifics
    t = re.sub(r"\b(sri|smt|mr|ms|mrs|dr|kumari|shri)\b\.?", "", t)
    # Strip special punctuation
    t = re.sub(r"[,\.\-\/\\\#]", " ", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t

def compute_similarity(s1: str, s2: str) -> float:
    """Compute string similarity ratio (0.0 to 1.0) handling token reordering."""
    n1 = normalize_text(s1)
    n2 = normalize_text(s2)
    if not n1 and not n2:
        return 1.0
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0

    # Sequence matcher ratio
    seq_ratio = difflib.SequenceMatcher(None, n1, n2).ratio()

    # Token sort ratio (e.g. "Sharma Rahul" vs "Rahul Sharma")
    t1 = " ".join(sorted(n1.split()))
    t2 = " ".join(sorted(n2.split()))
    token_ratio = difflib.SequenceMatcher(None, t1, t2).ratio()

    return max(seq_ratio, token_ratio)

def compare_dates(d1_str: str, d2_str: str) -> Tuple[bool, float, str]:
    """Compare dates canonically, returning (is_match, similarity_score, explanation)."""
    date1 = parse_date_string(d1_str)
    date2 = parse_date_string(d2_str)

    if date1 and date2:
        if date1 == date2:
            return True, 1.0, "Dates match exactly in canonical format."
        else:
            return False, 0.0, f"Date mismatch: '{d1_str}' ({date1}) vs '{d2_str}' ({date2})."
    
    # Fallback to string similarity if unparseable
    sim = compute_similarity(d1_str, d2_str)
    is_match = sim >= settings.SIMILARITY_THRESHOLD
    return is_match, sim, f"String date similarity score: {round(sim, 2)}"

def compare_incomes(inc1_str: str, inc2_str: str) -> Tuple[bool, float, str]:
    """Compare income figures by extracting numbers."""
    nums1 = re.findall(r"\d+", inc1_str.replace(",", ""))
    nums2 = re.findall(r"\d+", inc2_str.replace(",", ""))

    if nums1 and nums2:
        val1 = int("".join(nums1))
        val2 = int("".join(nums2))
        if val1 == val2:
            return True, 1.0, f"Income values match exactly (₹{val1:,})."
        else:
            diff = abs(val1 - val2)
            return False, 0.0, f"Conflicting income declarations: ₹{val1:,} vs ₹{val2:,} (difference: ₹{diff:,})."
    
    sim = compute_similarity(inc1_str, inc2_str)
    return sim >= settings.SIMILARITY_THRESHOLD, sim, "Non-numeric income comparison."

class CrossDocumentVerifier:
    """
    Implements Mode B: Multiple Document Cross-Verification.
    1. Verifies each document individually.
    2. Compares shared fields across all uploaded document pairs.
    3. Explains detected mismatches and grounds them in RAG.
    4. Aggregates results and prepares combined verification record.
    """

    @staticmethod
    def verify_multiple(documents: List[Document], db: Session) -> Dict[str, Any]:
        if len(documents) < 2:
            raise ValueError("Cross-verification requires at least two uploaded documents.")

        all_issues: List[Dict[str, Any]] = []
        individual_results: List[Dict[str, Any]] = []
        comparisons: List[Dict[str, Any]] = []

        # Step 1: Run individual verification for every document
        for doc in documents:
            ind_res = SingleDocumentVerifier.verify_document(doc, db)
            individual_results.append({
                "document_id": doc.id,
                "document_name": doc.original_filename,
                "category": doc.category,
                "overall_status": ind_res["overall_status"],
                "total_issues": ind_res["total_issues"],
                "issues": ind_res["issues"]
            })
            all_issues.extend(ind_res["issues"])

        # Step 2: Build field lookup maps for each document
        doc_fields_map: Dict[int, Dict[str, str]] = {}
        for doc in documents:
            doc_fields_map[doc.id] = {
                ef.field_name: ef.field_value for ef in doc.extracted_fields if ef.field_value
            }

        # Step 3: Compare shared fields across all document pairs
        compared_pairs = set()
        fields_to_compare = [
            ("full_name", "Full Name", "mismatch_name"),
            ("dob", "Date of Birth", "mismatch_dob"),
            ("address", "Address", "mismatch_address"),
            ("annual_income", "Annual Income", "mismatch_income"),
            ("institution_name", "Institution Name", "mismatch_institution"),
            ("academic_year", "Academic Year", "mismatch_academic_year")
        ]

        for i in range(len(documents)):
            for j in range(i + 1, len(documents)):
                doc_a = documents[i]
                doc_b = documents[j]
                pair_key = (min(doc_a.id, doc_b.id), max(doc_a.id, doc_b.id))
                if pair_key in compared_pairs:
                    continue
                compared_pairs.add(pair_key)

                fields_a = doc_fields_map[doc_a.id]
                fields_b = doc_fields_map[doc_b.id]

                for field_key, field_label, issue_category in fields_to_compare:
                    val_a = fields_a.get(field_key)
                    val_b = fields_b.get(field_key)

                    # Only compare if both documents contain this shared field
                    if not val_a or not val_b:
                        continue

                    is_match = False
                    similarity = 0.0
                    explanation = ""

                    if field_key == "dob":
                        is_match, similarity, explanation = compare_dates(val_a, val_b)
                    elif field_key == "annual_income":
                        is_match, similarity, explanation = compare_incomes(val_a, val_b)
                    else:
                        similarity = compute_similarity(val_a, val_b)
                        is_match = similarity >= settings.SIMILARITY_THRESHOLD
                        if is_match:
                            explanation = f"Values match with {int(similarity * 100)}% similarity."
                        else:
                            explanation = f"Value discrepancy detected ({int(similarity * 100)}% similarity)."

                    recommendation = "No correction required." if is_match else (
                        f"Ensure {field_label} is consistent across both {doc_a.category} and {doc_b.category} before submitting."
                    )

                    comparison_record = {
                        "field_name": field_label,
                        "doc_a_id": doc_a.id,
                        "doc_b_id": doc_b.id,
                        "doc_a_name": f"{doc_a.original_filename} ({doc_a.category})",
                        "doc_b_name": f"{doc_b.original_filename} ({doc_b.category})",
                        "val_a": val_a,
                        "val_b": val_b,
                        "is_match": is_match,
                        "similarity_score": round(similarity, 3),
                        "difference_explanation": explanation,
                        "recommendation": recommendation
                    }
                    comparisons.append(comparison_record)

                    # If there is a mismatch, generate a cross-document issue
                    if not is_match:
                        # RAG explanation
                        issue_info = rag_engine.generate_explanation(
                            issue_title=f"Cross-Document Mismatch: {field_label}",
                            category=doc_a.category,
                            evidence=f"{doc_a.original_filename}: '{val_a}' vs {doc_b.original_filename}: '{val_b}'",
                            expected_val=val_a,
                            actual_val=val_b
                        )

                        severity = "critical" if field_key in ("full_name", "dob") else "high"

                        all_issues.append({
                            "title": f"Cross-Document Mismatch: {field_label}",
                            "category": "confirmed_error" if severity == "critical" else "possible_inconsistencies",
                            "severity": severity,
                            "document_name": f"{doc_a.original_filename} & {doc_b.original_filename}",
                            "page_number": 1,
                            "evidence_snippet": f"Field '{field_label}': '{val_a}' vs '{val_b}' (similarity {int(similarity * 100)}%)",
                            "expected_value": val_a,
                            "actual_value": val_b,
                            "explanation": issue_info["explanation"],
                            "suggested_correction": issue_info["suggested_correction"],
                            "confidence_score": 0.95,
                            "manual_review_recommended": (similarity > 0.70 and not is_match),
                            "rag_rule_id": issue_info["rag_rule_id"],
                            "rag_source": issue_info["rag_source"]
                        })

        # Step 4: Overall Status Computation
        critical_count = sum(1 for i in all_issues if i["severity"] == "critical")
        warning_count = sum(1 for i in all_issues if i["severity"] in ("high", "medium", "low"))
        manual_review_needed = any(i.get("manual_review_recommended", False) for i in all_issues)

        if critical_count > 0:
            overall_status = "Needs Correction"
        elif manual_review_needed:
            overall_status = "Manual Review Required"
        elif warning_count > 0:
            overall_status = "Passed with Warnings"
        else:
            overall_status = "Passed"

        summary = (
            f"Multi-document cross-verification of {len(documents)} documents completed with status '{overall_status}'. "
            f"Evaluated {len(comparisons)} shared field comparisons; found {critical_count} critical issues and {warning_count} warnings."
        )

        return {
            "overall_status": overall_status,
            "total_issues": len(all_issues),
            "critical_issues": critical_count,
            "warning_issues": warning_count,
            "summary": summary,
            "issues": all_issues,
            "individual_results": individual_results,
            "comparisons": comparisons
        }
