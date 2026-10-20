"""
ScamShield AI — Text Classification and Explainability Service

Loads the serialized TF-IDF + LogisticRegression model artifact, performs microsecond
fraud inference, and extracts top explainability token coefficients.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "app" / "models" / "text_model.joblib"


@dataclass
class TextAnalysisResult:
    """Structured result returned by the text classification engine."""
    provided: bool = False
    risk_score: int = 0
    probability: float = 0.0
    detected_patterns: List[str] = field(default_factory=list)
    key_tokens: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize result to a dictionary matching the API contract."""
        return {
            "provided": self.provided,
            "risk_score": self.risk_score,
            "probability": round(self.probability, 4),
            "detected_patterns": self.detected_patterns,
            "key_tokens": self.key_tokens,
        }


class TextAnalyzer:
    """Singleton service wrapping the trained text classification pipeline."""

    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self._bundle: Optional[Dict] = None
        self._load_model()

    def _load_model(self):
        """Loads serialized model pipeline and vocabulary from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {self.model_path}. "
                "Run 'python scripts/train.py' first."
            )
        self._bundle = joblib.load(self.model_path)
        self.vectorizer = self._bundle["vectorizer"]
        self.calibrated_model = self._bundle["calibrated_model"]
        self.base_classifier = self._bundle["base_classifier"]
        self.feature_names = self._bundle["feature_names"]
        self.coef = self.base_classifier.coef_[0]

    def is_loaded(self) -> bool:
        """Returns True if model bundle is loaded and ready for inference."""
        return self._bundle is not None and self.calibrated_model is not None

    def _extract_patterns(self, text: str) -> List[str]:
        """Categorizes flagged language into understandable semantic pattern tags."""
        patterns = []
        lower = text.lower()

        urgency_terms = ["immediately", "urgent", "24 hours", "tonight", "hours", "expires", "suspended", "cutoff", "terminated"]
        found_urgency = [t for t in urgency_terms if t in lower]
        if found_urgency:
            patterns.append(f"High urgency language ('{found_urgency[0]}', '{found_urgency[1]}' if len(found_urgency) > 1 else 'urgent')")

        threat_terms = ["blocked", "disconnected", "penalty", "arrest", "court", "freeze", "deactivated", "legal"]
        found_threats = [t for t in threat_terms if t in lower]
        if found_threats:
            patterns.append(f"Financial penalty or service disruption pressure ('{found_threats[0]}')")

        credential_terms = ["otp", "pin", "password", "pan card", "aadhaar", "kyc", "verify", "login", "credentials"]
        found_creds = [t for t in credential_terms if t in lower]
        if found_creds:
            patterns.append(f"Sensitive credential or identity verification demands ('{found_creds[0]}')")

        lure_terms = ["won", "winner", "lottery", "cash prize", "bonus", "reward", "refund", "gift card"]
        found_lures = [t for t in lure_terms if t in lower]
        if found_lures:
            patterns.append(f"Unsolicited prize, lottery, or financial lure ('{found_lures[0]}')")

        job_terms = ["part-time", "daily payout", "work from home", "like youtube", "review products"]
        found_jobs = [t for t in job_terms if t in lower]
        if found_jobs:
            patterns.append("Unsolicited task or part-time job employment lure")

        if not patterns:
            patterns.append("Standard conversational or transactional phrasing observed")

        return patterns

    def _extract_key_tokens(self, text: str, prob_scam: float, top_n: int = 5) -> List[str]:
        """
        Extracts top tokens pushing the decision towards scam (or safe)
        via the dot product of TF-IDF feature weights and model coefficients.
        """
        X_vec = self.vectorizer.transform([text])
        feature_indices = X_vec.indices
        feature_values = X_vec.data

        if len(feature_indices) == 0:
            return []

        # Calculate word contribution: tfidf_weight * linear_coefficient
        word_contributions: List[Tuple[str, float]] = []
        for idx, val in zip(feature_indices, feature_values):
            word = self.feature_names[idx]
            weight = self.coef[idx] * val
            word_contributions.append((word, weight))

        # If scam probability is significant, sort by highest positive contributions
        if prob_scam >= 0.35:
            word_contributions.sort(key=lambda item: item[1], reverse=True)
            # Pick top tokens with positive weight
            selected = [w for w, score in word_contributions if score > 0][:top_n]
        else:
            # Otherwise, sort by lowest (most negative / safest) contributions
            word_contributions.sort(key=lambda item: item[1])
            selected = [w for w, score in word_contributions if score < 0][:top_n]

        # Fallback if no specific coefficients matched
        if not selected:
            selected = [w for w, _ in word_contributions[:top_n]]

        return selected

    def analyze_text(self, text: Optional[str]) -> TextAnalysisResult:
        """
        Runs inference on input message string.

        Returns:
            TextAnalysisResult with integer risk score (0-100), probability,
            explainable tokens, and detected semantic patterns.
        """
        if not text or not text.strip():
            return TextAnalysisResult(provided=False, risk_score=0, probability=0.0)

        clean_input = re.sub(r"\s+", " ", text).strip()
        # Cap input length at 10,000 characters as defined in security policy
        clean_input = clean_input[:10000]

        X_vec = self.vectorizer.transform([clean_input])
        prob_scam = float(self.calibrated_model.predict_proba(X_vec)[0, 1])

        risk_score = int(round(prob_scam * 100))
        risk_score = max(0, min(100, risk_score))

        patterns = self._extract_patterns(clean_input)
        key_tokens = self._extract_key_tokens(clean_input, prob_scam)

        return TextAnalysisResult(
            provided=True,
            risk_score=risk_score,
            probability=prob_scam,
            detected_patterns=patterns,
            key_tokens=key_tokens,
        )


# Global singleton instance
_analyzer_instance: Optional[TextAnalyzer] = None


def get_text_analyzer() -> TextAnalyzer:
    """Returns the singleton TextAnalyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = TextAnalyzer()
    return _analyzer_instance


def analyze_text(text: Optional[str]) -> TextAnalysisResult:
    """Convenience functional interface for text analysis."""
    return get_text_analyzer().analyze_text(text)
