import re
from typing import Dict, Any, List, Optional
import datetime
import logging

logger = logging.getLogger("evidencerag.extractor")

def parse_date_string(date_str: str) -> Optional[datetime.date]:
    """Parse various date formats into datetime.date."""
    date_str = date_str.strip()
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y",
        "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

class FieldExtractor:
    """
    Extracts structured fields from raw document text using pattern matching,
    anchor keyword searches, and regular expressions.
    """

    @staticmethod
    def extract_all_fields(raw_text: str, category: str, page_number: int = 1) -> List[Dict[str, Any]]:
        extracted = []
        text_lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        # 1. Full Name / Applicant Name / Student Name
        name_info = FieldExtractor._extract_name(raw_text, text_lines, category)
        if name_info:
            extracted.append({
                "field_name": "full_name",
                "field_value": name_info["value"],
                "confidence": name_info["confidence"],
                "page_number": page_number,
                "extraction_method": name_info["method"]
            })

        # 2. Date of Birth (DOB)
        dob_info = FieldExtractor._extract_dob(raw_text)
        if dob_info:
            extracted.append({
                "field_name": "dob",
                "field_value": dob_info["value"],
                "confidence": dob_info["confidence"],
                "page_number": page_number,
                "extraction_method": dob_info["method"]
            })

        # 3. Aadhaar Number (if Aadhaar or general ID)
        aadhaar_info = FieldExtractor._extract_aadhaar(raw_text)
        if aadhaar_info:
            extracted.append({
                "field_name": "aadhaar_number",
                "field_value": aadhaar_info["value"],
                "confidence": aadhaar_info["confidence"],
                "page_number": page_number,
                "extraction_method": aadhaar_info["method"]
            })

        # 4. Gender
        gender_info = FieldExtractor._extract_gender(raw_text)
        if gender_info:
            extracted.append({
                "field_name": "gender",
                "field_value": gender_info["value"],
                "confidence": gender_info["confidence"],
                "page_number": page_number,
                "extraction_method": gender_info["method"]
            })

        # 5. Certificate Number / Document Identifier
        cert_no_info = FieldExtractor._extract_cert_number(raw_text, category)
        if cert_no_info:
            extracted.append({
                "field_name": "certificate_number",
                "field_value": cert_no_info["value"],
                "confidence": cert_no_info["confidence"],
                "page_number": page_number,
                "extraction_method": cert_no_info["method"]
            })

        # 6. Issue Date
        issue_date_info = FieldExtractor._extract_issue_date(raw_text)
        if issue_date_info:
            extracted.append({
                "field_name": "issue_date",
                "field_value": issue_date_info["value"],
                "confidence": issue_date_info["confidence"],
                "page_number": page_number,
                "extraction_method": issue_date_info["method"]
            })

        # 7. Expiry Date / Valid Upto
        expiry_date_info = FieldExtractor._extract_expiry_date(raw_text)
        if expiry_date_info:
            extracted.append({
                "field_name": "expiry_date",
                "field_value": expiry_date_info["value"],
                "confidence": expiry_date_info["confidence"],
                "page_number": page_number,
                "extraction_method": expiry_date_info["method"]
            })

        # 8. Annual Income Amount
        if category in ("Income Certificate", "Other Supporting Documents"):
            income_info = FieldExtractor._extract_income(raw_text)
            if income_info:
                extracted.append({
                    "field_name": "annual_income",
                    "field_value": income_info["value"],
                    "confidence": income_info["confidence"],
                    "page_number": page_number,
                    "extraction_method": income_info["method"]
                })

        # 9. Caste Category
        if category in ("Caste Certificate", "Other Supporting Documents"):
            caste_info = FieldExtractor._extract_caste(raw_text)
            if caste_info:
                extracted.append({
                    "field_name": "caste_category",
                    "field_value": caste_info["value"],
                    "confidence": caste_info["confidence"],
                    "page_number": page_number,
                    "extraction_method": caste_info["method"]
                })

        # 10. Address
        address_info = FieldExtractor._extract_address(raw_text)
        if address_info:
            extracted.append({
                "field_name": "address",
                "field_value": address_info["value"],
                "confidence": address_info["confidence"],
                "page_number": page_number,
                "extraction_method": address_info["method"]
            })

        # 11. Institution Name / School / College
        if category in ("Study Certificate", "Bonafide Certificate", "Marks Memo", "Other Supporting Documents"):
            inst_info = FieldExtractor._extract_institution(raw_text)
            if inst_info:
                extracted.append({
                    "field_name": "institution_name",
                    "field_value": inst_info["value"],
                    "confidence": inst_info["confidence"],
                    "page_number": page_number,
                    "extraction_method": inst_info["method"]
                })

        # 12. Academic Year
        acad_info = FieldExtractor._extract_academic_year(raw_text)
        if acad_info:
            extracted.append({
                "field_name": "academic_year",
                "field_value": acad_info["value"],
                "confidence": acad_info["confidence"],
                "page_number": page_number,
                "extraction_method": acad_info["method"]
            })

        # 13. Bank Account & IFSC
        if category in ("Bank Passbook", "Other Supporting Documents"):
            bank_acc_info = FieldExtractor._extract_bank_account(raw_text)
            if bank_acc_info:
                extracted.append({
                    "field_name": "account_number",
                    "field_value": bank_acc_info["value"],
                    "confidence": bank_acc_info["confidence"],
                    "page_number": page_number,
                    "extraction_method": bank_acc_info["method"]
                })
            
            ifsc_info = FieldExtractor._extract_ifsc(raw_text)
            if ifsc_info:
                extracted.append({
                    "field_name": "ifsc_code",
                    "field_value": ifsc_info["value"],
                    "confidence": ifsc_info["confidence"],
                    "page_number": page_number,
                    "extraction_method": ifsc_info["method"]
                })

        return extracted

    @staticmethod
    def _extract_name(text: str, lines: List[str], category: str) -> Optional[Dict[str, Any]]:
        # Patterns like: Name: John Doe, Student Name: John Doe, This is to certify that Sri/Mr. John Doe
        patterns = [
            r"(?:Name|Applicant Name|Student Name|Candidate Name|Account Holder Name|Sri|Smt|Mr\.|Ms\.)\s*[:\-\.]\s*([A-Za-z\s\.]{3,50})",
            r"(?:This is to certify that|certify that)\s+(?:Sri|Smt|Kumari|Sri\/Kumari|Mr\.|Ms\.)?\s*([A-Za-z\s\.]{3,50})[,\s]+(?:Son|Daughter|S\/o|D\/o|Son\/Daughter|is a bonafide|bearing|residing)",
            r"(?:Name)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                # Clean trailing noise
                val = re.sub(r"\s+(?:Son of|Daughter of|S/o|D/o|is|bearing|aged|resident|residing).*", "", val, flags=re.IGNORECASE).strip()
                if len(val) >= 3 and not val.lower().startswith("is a"):
                    return {"value": val, "confidence": 0.95, "method": "regex_anchor"}

        # Search line-by-line for Name header
        for idx, line in enumerate(lines):
            if re.match(r"^(?:Name|Full Name|Applicant Name|Student Name)$", line, re.IGNORECASE) and idx + 1 < len(lines):
                next_val = lines[idx + 1].strip()
                if len(next_val) >= 3 and re.match(r"^[A-Za-z\s\.]+$", next_val):
                    return {"value": next_val, "confidence": 0.88, "method": "layout_header"}

        return None

    @staticmethod
    def _extract_dob(text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:DOB|Date of Birth|Birth Date)\s*[:\-\.]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})",
            r"(?:DOB|Date of Birth)\s*[:\-\.]\s*(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})",
            r"(?:DOB|Date of Birth)\s*[:\-\.]\s*(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})",
            r"(?:born on)\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return {"value": match.group(1).strip(), "confidence": 0.95, "method": "regex_dob"}
        return None

    @staticmethod
    def _extract_aadhaar(text: str) -> Optional[Dict[str, Any]]:
        # 12 digits, often formatted as 4-4-4
        match = re.search(r"\b(\d{4}\s\d{4}\s\d{4})\b", text)
        if match:
            return {"value": match.group(1).strip(), "confidence": 0.98, "method": "regex_aadhaar"}
        
        match_unspaced = re.search(r"(?:Aadhaar|UID|Aadhaar No)\s*[:\-\.]\s*(\d{12})\b", text, re.IGNORECASE)
        if match_unspaced:
            num = match_unspaced.group(1)
            formatted = f"{num[:4]} {num[4:8]} {num[8:]}"
            return {"value": formatted, "confidence": 0.92, "method": "regex_aadhaar_unspaced"}
        return None

    @staticmethod
    def _extract_gender(text: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"\b(?:Gender|Sex)\s*[:\-\.]\s*(Male|Female|Transgender|M|F)\b", text, re.IGNORECASE)
        if match:
            g = match.group(1).upper()
            if g == "M": g = "Male"
            elif g == "F": g = "Female"
            return {"value": g.capitalize(), "confidence": 0.92, "method": "regex_gender"}
        return None

    @staticmethod
    def _extract_cert_number(text: str, category: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:Certificate No|Certificate Number|Cert No|Application No|Ref No|Roll No|Hall Ticket No|Regd No)\s*[:\-\.]\s*([A-Za-z0-9\-\/]{5,30})",
            r"\b([A-Z]{2,4}\/[0-9]{4}\/[0-9]{4,8})\b",
            r"\b(INC\d{8,12}|CST\d{8,12}|RES\d{8,12}|STU\d{8,12}|BON\d{8,12})\b"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return {"value": match.group(1).strip(), "confidence": 0.93, "method": "regex_cert_no"}
        return None

    @staticmethod
    def _extract_issue_date(text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:Date of Issue|Issue Date|Issued on|Date)\s*[:\-\.]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})",
            r"(?:Date of Issue|Issue Date)\s*[:\-\.]\s*(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return {"value": match.group(1).strip(), "confidence": 0.94, "method": "regex_issue_date"}
        return None

    @staticmethod
    def _extract_expiry_date(text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:Valid Upto|Valid Till|Expiry Date|Expires on|Valid until)\s*[:\-\.]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})",
            r"(?:Valid Upto|Valid Till|Expiry Date)\s*[:\-\.]\s*(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return {"value": match.group(1).strip(), "confidence": 0.94, "method": "regex_expiry_date"}
        return None

    @staticmethod
    def _extract_income(text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:Annual Income|Total Income|Family Income|Annual Family Income|Income)\s*[:\-\.]\s*(?:Rs\.?|INR|₹|I)?\s*([0-9,]{4,10})",
            r"(?:Rs\.?|INR|₹)\s*([0-9,]{4,10})\s*(?:per annum|\/\-|\s+only)",
            r"(?:Rupees)\s+([A-Za-z\s]+only)"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                # Clean commas
                clean_num = val.replace(",", "")
                if clean_num.isdigit():
                    return {"value": f"₹{int(clean_num):,}", "confidence": 0.95, "method": "regex_income"}
                return {"value": val, "confidence": 0.85, "method": "regex_income_words"}
        return None

    @staticmethod
    def _extract_caste(text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:Category|Community|Caste)\s*[:\-\.]\s*([A-Za-z0-9\-\s\(\)]{2,25})",
            r"\b(SC|ST|OBC|EWS|General|BC-A|BC-B|BC-C|BC-D|BC-E)\b"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                return {"value": val, "confidence": 0.92, "method": "regex_caste"}
        return None

    @staticmethod
    def _extract_address(text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:Address|Permanent Address|Residential Address)\s*[:\-\.]\s*([A-Za-z0-9\s,\-\.\#\/]{10,120}(?:\d{6})?)",
            r"(?:Residing at|Resident of)\s*[:\-\.]?\s*([A-Za-z0-9\s,\-\.\#\/]{10,120})"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                # Remove trailing newlines or keywords
                val = val.split("\n")[0].strip()
                return {"value": val, "confidence": 0.88, "method": "regex_address"}
        return None

    @staticmethod
    def _extract_institution(text: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"(?:Institution|College|School|University|Studying in)\s*[:\-\.]\s*([A-Za-z0-9\s,\.\(\)\-]{5,80})",
            r"(?:National Institute of Technology|Indian Institute of Technology|Government Polytechnic|University of [A-Za-z]+|[A-Za-z\s]+College of Engineering|[A-Za-z\s]+High School)",
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = (match.group(1) if match.groups() else match.group(0)).strip()
                val = val.split("\n")[0].strip()
                return {"value": val, "confidence": 0.90, "method": "regex_institution"}
        return None

    @staticmethod
    def _extract_academic_year(text: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"\b(20\d{2}\s*[\-\/]\s*20\d{2}|20\d{2}\s*[\-\/]\s*\d{2})\b", text)
        if match:
            return {"value": match.group(1).strip(), "confidence": 0.95, "method": "regex_academic_year"}
        return None

    @staticmethod
    def _extract_bank_account(text: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"(?:Account No|A\/C No|Account Number)\s*[:\-\.]\s*([0-9]{9,18})\b", text, re.IGNORECASE)
        if match:
            return {"value": match.group(1).strip(), "confidence": 0.95, "method": "regex_bank_account"}
        return None

    @staticmethod
    def _extract_ifsc(text: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", text)
        if match:
            return {"value": match.group(1).strip(), "confidence": 0.98, "method": "regex_ifsc"}
        return None
