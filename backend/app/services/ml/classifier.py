import os
import joblib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from backend.app.core.config import settings

logger = logging.getLogger("evidencerag.ml")

MODEL_PATH = settings.MODELS_DIR / "document_classifier.joblib"

class DocumentClassifier:
    """
    Classifies documents into the 10 scholarship document categories based on raw OCR text.
    """

    def __init__(self):
        self.model: Optional[Pipeline] = None
        self.load_model()

    def load_model(self):
        if MODEL_PATH.exists():
            try:
                self.model = joblib.load(str(MODEL_PATH))
                logger.info(f"Loaded trained document classifier from {MODEL_PATH}")
            except Exception as e:
                logger.error(f"Error loading classifier model: {e}")
                self.model = None

    def predict(self, text: str) -> Dict[str, Any]:
        """Predict document category and confidence score."""
        if not self.model or not text.strip():
            # Heuristic keyword fallback if model is not yet loaded
            return self._heuristic_fallback(text)

        try:
            probas = self.model.predict_proba([text])[0]
            classes = self.model.classes_
            best_idx = probas.argmax()
            predicted_class = classes[best_idx]
            confidence = float(probas[best_idx])

            return {
                "predicted_category": str(predicted_class),
                "confidence": round(confidence, 3),
                "model": "TF-IDF + Logistic Regression"
            }
        except Exception as e:
            logger.warning(f"Prediction failed, using fallback: {e}")
            return self._heuristic_fallback(text)

    def _heuristic_fallback(self, text: str) -> Dict[str, Any]:
        t = text.lower()
        if "aadhaar" in t or "unique identification" in t:
            return {"predicted_category": "Aadhaar Card", "confidence": 0.85, "model": "Heuristic Rule"}
        elif "annual income" in t or "income certificate" in t:
            return {"predicted_category": "Income Certificate", "confidence": 0.85, "model": "Heuristic Rule"}
        elif "caste" in t or "community certificate" in t:
            return {"predicted_category": "Caste Certificate", "confidence": 0.85, "model": "Heuristic Rule"}
        elif "residence" in t or "domicile" in t:
            return {"predicted_category": "Residence Certificate", "confidence": 0.85, "model": "Heuristic Rule"}
        elif "bonafide" in t:
            return {"predicted_category": "Bonafide Certificate", "confidence": 0.85, "model": "Heuristic Rule"}
        elif "study certificate" in t or "studying in" in t:
            return {"predicted_category": "Study Certificate", "confidence": 0.85, "model": "Heuristic Rule"}
        elif "marks memo" in t or "grade sheet" in t or "hall ticket" in t:
            return {"predicted_category": "Marks Memo", "confidence": 0.85, "model": "Heuristic Rule"}
        elif "passbook" in t or "savings bank" in t or "ifsc" in t:
            return {"predicted_category": "Bank Passbook", "confidence": 0.85, "model": "Heuristic Rule"}
        return {"predicted_category": "Other Supporting Documents", "confidence": 0.70, "model": "Heuristic Rule"}

# Global singleton classifier
document_classifier = DocumentClassifier()
