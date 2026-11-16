import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from backend.app.core.config import settings
from backend.app.services.rag.knowledge_base import KNOWLEDGE_RULES

logger = logging.getLogger("evidencerag.rag")

class RAGEngine:
    """
    Retrieval-Augmented Generation engine for EvidenceRAG:
    - Maintains indexed verification rules
    - Performs semantic/vector retrieval of relevant regulatory guidelines
    - Interfaces with Ollama LLM (Qwen/Llama) with robust deterministic fallback
    """

    def __init__(self):
        self.rules: List[Dict[str, Any]] = KNOWLEDGE_RULES
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        
        # Build search index
        self.reindex()

    def reindex(self):
        """Rebuild TF-IDF search index from current rules."""
        corpus = [
            f"{r['category']} {r['title']} {r['content']} {' '.join(r.get('mandatory_fields', []))}"
            for r in self.rules
        ]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        logger.info(f"RAG Engine indexed with {len(self.rules)} knowledge rules.")

    def add_rule(self, rule_data: Dict[str, Any]):
        self.rules.append(rule_data)
        self.reindex()

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for r in self.rules:
            if r["id"] == rule_id:
                r.update({k: v for k, v in updates.items() if v is not None})
                self.reindex()
                return r
        return None

    def delete_rule(self, rule_id: str) -> bool:
        initial_len = len(self.rules)
        self.rules = [r for r in self.rules if r["id"] != rule_id]
        if len(self.rules) < initial_len:
            self.reindex()
            return True
        return False

    def retrieve(self, query: str, category: Optional[str] = None, top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieve most relevant rules based on query and document category."""
        # Query TF-IDF representation
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix)[0]

        scored_rules = []
        for idx, rule in enumerate(self.rules):
            score = float(sims[idx])
            # Boost score if category matches
            if category and rule["category"].lower() == category.lower():
                score += 0.35
            scored_rules.append((score, rule))

        scored_rules.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, r in scored_rules[:top_k]:
            results.append({
                "rule_id": r["id"],
                "category": r["category"],
                "title": r["title"],
                "content": r["content"],
                "source": r["source"],
                "similarity_score": round(min(1.0, score), 3)
            })
        return results

    def generate_explanation(
        self,
        issue_title: str,
        category: str,
        evidence: Optional[str] = None,
        expected_val: Optional[str] = None,
        actual_val: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate evidence-grounded explanation for a detected issue using RAG.
        Attempts LLM generation via Ollama; falls back deterministically if Ollama is unavailable.
        """
        query = f"{category} {issue_title} expected {expected_val} actual {actual_val} {evidence or ''}"
        retrieved = self.retrieve(query=query, category=category, top_k=1)
        top_rule = retrieved[0] if retrieved else {
            "rule_id": "DEFAULT-RULE",
            "source": "Standard Scholarship Document Verification Policy",
            "content": "All submitted application documents must be authentic, valid, unexpired, and complete.",
            "title": "General Application Policy"
        }

        # Check if Ollama LLM is reachable
        ollama_response = self._try_ollama_generation(
            issue_title=issue_title,
            category=category,
            evidence=evidence,
            expected_val=expected_val,
            actual_val=actual_val,
            rule=top_rule
        )

        if ollama_response:
            return {
                "explanation": ollama_response.get("explanation"),
                "suggested_correction": ollama_response.get("suggested_correction"),
                "rag_rule_id": top_rule.get("rule_id"),
                "rag_source": top_rule.get("source"),
                "retrieved_context": top_rule.get("content"),
                "llm_used": True,
                "model_name": settings.OLLAMA_MODEL,
                "confidence": 0.94
            }

        # Deterministic fallback grounded in retrieved rule
        fallback_explanation = self._build_deterministic_explanation(
            issue_title=issue_title,
            category=category,
            evidence=evidence,
            expected_val=expected_val,
            actual_val=actual_val,
            rule=top_rule
        )

        return {
            "explanation": fallback_explanation["explanation"],
            "suggested_correction": fallback_explanation["suggested_correction"],
            "rag_rule_id": top_rule.get("rule_id"),
            "rag_source": top_rule.get("source"),
            "retrieved_context": top_rule.get("content"),
            "llm_used": False,
            "model_name": "Deterministic RAG Fallback",
            "confidence": 0.90
        }

    def _try_ollama_generation(
        self,
        issue_title: str,
        category: str,
        evidence: Optional[str],
        expected_val: Optional[str],
        actual_val: Optional[str],
        rule: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """Send prompt to local Ollama instance if active."""
        prompt = f"""You are EvidenceRAG, an explainable document verification AI for student scholarships.
Grounded Knowledge Source: {rule.get('source')}
Regulatory Guideline: {rule.get('content')}

Detected Issue: {issue_title}
Document Category: {category}
Evidence Snippet: {evidence or 'Not available'}
Expected Value: {expected_val or 'Standard verified format'}
Actual Value: {actual_val or 'Missing or malformed'}

Provide a concise, grounded explanation of why this issue matters under the rule, and an actionable suggested correction for the student.
Respond ONLY with a JSON object in this format:
{{"explanation": "...", "suggested_correction": "..."}}
"""
        try:
            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            # Short timeout to avoid blocking if Ollama daemon is not running
            response = httpx.post(url, json=payload, timeout=2.0)
            if response.status_code == 200:
                raw_out = response.json().get("response", "")
                parsed = json.loads(raw_out)
                if "explanation" in parsed and "suggested_correction" in parsed:
                    return parsed
        except Exception:
            # Expected when Ollama is not installed or running
            pass
        return None

    def _build_deterministic_explanation(
        self,
        issue_title: str,
        category: str,
        evidence: Optional[str],
        expected_val: Optional[str],
        actual_val: Optional[str],
        rule: Dict[str, Any]
    ) -> Dict[str, str]:
        """Produce high-quality, regulation-grounded deterministic explanations."""
        title_lower = issue_title.lower()

        if "missing" in title_lower and "field" in title_lower:
            field_name = expected_val or "mandatory field"
            explanation = (
                f"The {field_name} could not be extracted from the uploaded {category}. "
                f"Under {rule.get('source', 'configured scholarship requirements')}, this document type strictly requires "
                f"a legible {field_name} for official pre-submission verification. Missing attributes can lead to application disqualification."
            )
            correction = (
                f"Please inspect your physical or digital {category}. Ensure that the full {field_name} is clearly visible, "
                f"uncropped, and legible, then upload a refreshed scan."
            )

        elif "expired" in title_lower or "validity" in title_lower:
            explanation = (
                f"The certificate appears to have exceeded its designated validity period. "
                f"According to {rule.get('source')}, {category} documents have an active validity window "
                f"and must be current at the time of scholarship submission. Actual extracted issue/expiry details: '{actual_val or 'Outdated'}', "
                f"whereas an active, unexpired certificate is required."
            )
            correction = (
                f"Obtain a newly issued {category} from your local revenue authority/educational board "
                f"and upload the updated valid certificate."
            )

        elif "date" in title_lower or "format" in title_lower:
            explanation = (
                f"An irregular date representation was encountered: '{actual_val or 'invalid format'}'. "
                f"{rule.get('title')}: Date values must conform to valid Gregorian calendar dates "
                f"(expected format: {expected_val or 'DD/MM/YYYY'}). Impossible dates or non-standard syntax prevent automated portal validation."
            )
            correction = (
                f"Verify the date on the original document. If OCR misread the date due to scan distortion, "
                f"please upload a higher-contrast scan."
            )

        elif "blur" in title_lower or "quality" in title_lower or "resolution" in title_lower:
            explanation = (
                f"The uploaded document image failed legibility quality checks ({rule.get('title')}). "
                f"High optical blur or low resolution prevents reliable optical character extraction, "
                f"which risks automatic rejection during institutional audit."
            )
            correction = (
                "Scan or photograph the physical document under good lighting with a minimum resolution of 300 DPI. "
                "Avoid camera glare, shaky capture, and low-contrast photocopying."
            )

        elif "mismatch" in title_lower or "inconsistent" in title_lower:
            explanation = (
                f"A discrepancy was identified between document records. "
                f"Expected: '{expected_val or 'Primary ID Value'}', Actual: '{actual_val or 'Inconsistent Value'}'. "
                f"Cross-document consistency across {rule.get('category', 'credentials')} is strictly enforced "
                f"to prevent clerical errors and eligibility rejection."
            )
            correction = (
                "Review both uploaded documents to confirm whether this is a minor spelling variant, abbreviation, "
                "or clerical mistake. If a legitimate legal change has occurred, attach supporting gazette or affidavit proof."
            )

        elif "signature" in title_lower or "stamp" in title_lower:
            explanation = (
                f"Official issuing authority endorsement (signature/official seal) could not be definitively recognized in this {category}. "
                f"Per {rule.get('source')}, official credentials require verified attestation. "
                f"Note: This automated finding does not deem the certificate fraudulent, but flags it for manual review."
            )
            correction = (
                "Ensure that the full official page including issuing authority seal, signature, or digital e-Sign certificate "
                "is completely captured inside the scanned border."
            )

        else:
            explanation = (
                f"Issue identified in {category}: {issue_title}. "
                f"Per {rule.get('source')}, all submitted scholarship credentials must fulfill stated statutory guidelines "
                f"to guarantee seamless processing."
            )
            correction = (
                "Review the original document against official portal guidelines and upload a corrected or complete copy."
            )

        return {
            "explanation": explanation,
            "suggested_correction": correction
        }

# Global singleton RAG instance
rag_engine = RAGEngine()
