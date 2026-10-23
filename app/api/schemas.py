"""
ScamShield AI — Pydantic v2 Request & Response Data Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from app.config import settings


# -----------------------------------------------------------------------------
# Analysis Schemas
# -----------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Payload submitted for fraud and phishing analysis."""

    text: Optional[str] = Field(
        default=None,
        max_length=settings.MAX_TEXT_LENGTH,
        description="User message text to analyze (max 10,000 characters).",
    )
    url: Optional[str] = Field(
        default=None,
        max_length=settings.MAX_URL_LENGTH,
        description="URL or domain to analyze (max 2,048 characters).",
    )

    @model_validator(mode="after")
    def validate_at_least_one_input(self) -> "AnalyzeRequest":
        """Ensures that at least text or url contains non-whitespace content."""
        has_text = bool(self.text and self.text.strip())
        has_url = bool(self.url and self.url.strip())
        if not has_text and not has_url:
            raise ValueError("At least one of 'text' or 'url' must contain non-whitespace characters.")
        return self


class TextAnalysisResponse(BaseModel):
    """Granular text analysis breakdown and explainability tokens."""

    provided: bool
    risk_score: Optional[int] = None
    probability: Optional[float] = None
    detected_patterns: List[str] = Field(default_factory=list)
    key_tokens: List[str] = Field(default_factory=list)


class URLAnalysisResponse(BaseModel):
    """Granular lexical URL analysis breakdown and heuristic red flags."""

    provided: bool
    risk_score: Optional[int] = None
    target_domain: Optional[str] = None
    is_ip_address: Optional[bool] = None
    has_homoglyphs: Optional[bool] = None
    flagged_indicators: List[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    """Consolidated assessment output adhering to API contract §4.1."""

    verdict: str = Field(description="Three-state verdict: 'likely safe', 'needs review', or 'likely scam'.")
    risk_score: int = Field(ge=0, le=100, description="Normalized risk score from 0 (safest) to 100 (highest risk).")
    confidence: float = Field(ge=0.0, le=1.0, description="Normalized composite decision confidence / risk index (0.0 to 1.0).")
    summary: str = Field(description="Concise 1-sentence diagnostic explanation.")
    text_analysis: TextAnalysisResponse
    url_analysis: URLAnalysisResponse
    evidence: List[str] = Field(description="Plain-English evidence bullet points explaining the decision.")
    recommended_action: str = Field(description="Context-aware safety and defense recommendation.")
    analyzed_at: str = Field(description="ISO 8601 UTC timestamp of analysis completion.")


# -----------------------------------------------------------------------------
# System Health Schema
# -----------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Application health and runtime status model."""

    status: str
    app_name: str
    version: str
    model_loaded: bool
    classifier_type: str
    timestamp: str


# -----------------------------------------------------------------------------
# Benchmark Evaluation Schemas
# -----------------------------------------------------------------------------

class DatasetInfo(BaseModel):
    name: str
    total_samples: int
    train_samples: int
    val_samples: int
    test_samples: int
    stratified: bool


class MetricsInfo(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float


class ConfusionMatrixInfo(BaseModel):
    true_negatives: int
    false_positives: int
    false_negatives: int
    true_positives: int


class ThresholdStrategyInfo(BaseModel):
    scam_threshold: float
    review_threshold: float
    selected_on: str


class EvaluationResponse(BaseModel):
    """Formal benchmark evaluation results on the held-out test split."""

    dataset: DatasetInfo
    metrics: MetricsInfo
    confusion_matrix: ConfusionMatrixInfo
    threshold_strategy: ThresholdStrategyInfo
    verified_at: str
