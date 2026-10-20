"""
ScamShield AI — Unified Verdict Arbiter & Evidence Synthesis Engine

Combines text classification scores and lexical URL risk heuristics into a
single, explainable verdict with normalized risk scores, human-readable evidence
points, and context-aware protective recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config import settings
from app.services.text_analyzer import TextAnalysisResult
from app.services.url_analyzer import URLAnalysisResult


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------

@dataclass
class UnifiedVerdict:
    """Consolidated assessment synthesized across all input modalities."""

    verdict: str
    risk_score: int
    confidence: float
    summary: str
    text_analysis: Dict
    url_analysis: Dict
    evidence: List[str]
    recommended_action: str
    analyzed_at: str

    def to_dict(self) -> Dict:
        """Serialize unified verdict to API response format."""
        return {
            "verdict": self.verdict,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "summary": self.summary,
            "text_analysis": self.text_analysis,
            "url_analysis": self.url_analysis,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
            "analyzed_at": self.analyzed_at,
        }


# -----------------------------------------------------------------------------
# Arbiter Engine
# -----------------------------------------------------------------------------

class VerdictArbiter:
    """Multi-modal scoring policy, signal harmonization, and evidence generator."""

    def __init__(
        self,
        scam_threshold: int = settings.VERDICT_SCAM_THRESHOLD,
        review_threshold: int = settings.VERDICT_REVIEW_THRESHOLD,
    ):
        self.scam_threshold = scam_threshold
        self.review_threshold = review_threshold

    def compute_blended_score(
        self,
        text_result: Optional[TextAnalysisResult],
        url_result: Optional[URLAnalysisResult],
    ) -> int:
        """
        Computes the composite risk score (0-100) based on available modalities.

        Scoring Rules:
        - Text only: Text risk score.
        - URL only: URL risk score.
        - Dual mode: max(0.55 * Text + 0.45 * URL, 0.85 * max(Text, URL))
        - Critical override: Raw IP address with credential keywords escalates to scam.
        - Signal divergence: If |Text - URL| > 50, ensure minimum score >= review_threshold.
        """
        has_text = text_result is not None and text_result.provided
        has_url = url_result is not None and url_result.provided

        if not has_text and not has_url:
            raise ValueError("At least one analysis modality (text or URL) must be provided.")

        if has_text and not has_url:
            raw_score = text_result.risk_score
            return max(0, min(100, int(round(raw_score))))

        if has_url and not has_text:
            raw_score = url_result.risk_score
            # Critical override: IP address host with high URL risk
            if url_result.is_ip_address and raw_score >= 50:
                raw_score = max(raw_score, self.scam_threshold)
            return max(0, min(100, int(round(raw_score))))

        # Both modalities are provided
        t_score = float(text_result.risk_score)
        u_score = float(url_result.risk_score)

        # Standard dual-mode formula
        weighted_avg = (t_score * 0.55) + (u_score * 0.45)
        dominant_max = max(t_score, u_score) * 0.85
        blended = max(weighted_avg, dominant_max)

        # Critical override: IP address host + credential lure/urgency
        if url_result.is_ip_address:
            has_cred_tokens = any(
                tok in {"login", "verify", "password", "bank", "account", "security"}
                for tok in text_result.key_tokens
            )
            has_cred_patterns = any(
                "credential" in pat.lower() or "urgency" in pat.lower()
                for pat in text_result.detected_patterns
            )
            if has_cred_tokens or has_cred_patterns or u_score >= 50:
                blended = max(blended, float(self.scam_threshold))

        # Signal divergence escalation
        if abs(t_score - u_score) > 50.0:
            blended = max(blended, float(self.review_threshold))

        return max(0, min(100, int(round(blended))))

    def determine_verdict(self, risk_score: int) -> str:
        """Maps a 0-100 composite risk score to a 3-state categorical verdict."""
        if risk_score >= self.scam_threshold:
            return "likely scam"
        elif risk_score >= self.review_threshold:
            return "needs review"
        else:
            return "likely safe"

    def synthesize_evidence(
        self,
        verdict: str,
        risk_score: int,
        text_result: Optional[TextAnalysisResult],
        url_result: Optional[URLAnalysisResult],
    ) -> List[str]:
        """Synthesizes human-readable, accessible evidence bullet points."""
        evidence: List[str] = []
        has_text = text_result is not None and text_result.provided
        has_url = url_result is not None and url_result.provided

        # 1. Text evidence points
        if has_text:
            if text_result.detected_patterns:
                for pattern in text_result.detected_patterns[:3]:
                    evidence.append(f"Message content: {pattern}.")
            elif text_result.risk_score >= 50:
                evidence.append(
                    f"Message exhibits linguistic markers associated with scam lures "
                    f"(score: {text_result.risk_score}/100)."
                )

            if text_result.key_tokens and text_result.risk_score >= 40:
                flagged_words = ", ".join(f"'{tok}'" for tok in text_result.key_tokens[:5])
                evidence.append(f"High-risk keywords identified: {flagged_words}.")

            if text_result.risk_score < 20 and not text_result.detected_patterns:
                evidence.append("Message text does not display urgency, threats, or unverified payment lures.")

        # 2. URL evidence points
        if has_url:
            if url_result.flagged_indicators:
                for indicator in url_result.flagged_indicators[:4]:
                    evidence.append(f"Link security: {indicator}.")
            elif url_result.risk_score >= 50:
                evidence.append(
                    f"Link exhibits structural anomalies common in phishing campaigns "
                    f"(score: {url_result.risk_score}/100)."
                )

            if url_result.risk_score < 20 and not url_result.flagged_indicators:
                evidence.append("Target URL uses standard host formatting without recognized spoofing patterns.")

        # 3. Cross-modal divergence notice
        if has_text and has_url and abs(text_result.risk_score - url_result.risk_score) > 50:
            evidence.append(
                "Asymmetric risk detected: message text and destination URL exhibit divergent threat levels; "
                "the higher-risk element governs the evaluation."
            )

        # 4. Fallback safeguard for clear communication
        if not evidence:
            if verdict == "likely safe":
                evidence.append("Passive lexical and machine learning checks found no overt fraudulent signatures.")
            else:
                evidence.append(f"Composite security evaluation indicates an overall risk index of {risk_score}/100.")

        return evidence

    def generate_summary(
        self,
        verdict: str,
        risk_score: int,
        has_text: bool,
        has_url: bool,
    ) -> str:
        """Produces a concise 1-sentence diagnostic summary."""
        if verdict == "likely scam":
            if has_text and has_url:
                return "High-risk scam and phishing indicators detected across both message content and embedded URL."
            elif has_url:
                return "Severe phishing and evasion indicators detected in the submitted destination link."
            else:
                return "High-urgency manipulation, credential lures, or payment demands detected in message text."

        if verdict == "needs review":
            if has_text and has_url:
                return "Moderate risk or conflicting signals detected between message content and URL destination."
            elif has_url:
                return "Unusual link formatting or uncommon domain structure warrants verification before proceeding."
            else:
                return "Message contains ambiguous urgency or financial keywords that require user verification."

        # likely safe
        if has_text and has_url:
            return "No overt scam or phishing patterns detected in either the message text or the URL."
        elif has_url:
            return "Link structure appears consistent with standard legitimate web services."
        else:
            return "Message content does not exhibit typical fraudulent phrasing or psychological pressure."

    def generate_recommended_action(self, verdict: str) -> str:
        """Produces actionable, context-aware user safety guidance."""
        if verdict == "likely scam":
            return (
                "Do not open the link, download attachments, or share passwords, OTPs, or financial details. "
                "If this communication claims to originate from your bank or an essential service, verify it "
                "independently using their official application or published customer service line."
            )
        elif verdict == "needs review":
            return (
                "Proceed with caution. Independently confirm the sender's identity through a trusted, separate "
                "channel before clicking any links, logging into accounts, or transferring funds."
            )
        else:
            return (
                "Content appears standard. Maintain routine digital hygiene: always check the browser address bar "
                "before submitting credentials, and never share one-time passcodes."
            )

    def synthesize(
        self,
        text_result: Optional[TextAnalysisResult] = None,
        url_result: Optional[URLAnalysisResult] = None,
    ) -> UnifiedVerdict:
        """
        Synthesizes individual modality results into a complete UnifiedVerdict.

        Args:
            text_result: Result from TextAnalyzer, or None if text was not provided.
            url_result: Result from URLAnalyzer, or None if URL was not provided.

        Returns:
            UnifiedVerdict containing normalized score, 3-state verdict, evidence, and advice.
        """
        has_text = text_result is not None and text_result.provided
        has_url = url_result is not None and url_result.provided

        if not has_text and not has_url:
            raise ValueError("Cannot synthesize verdict: both text and URL analyses are empty.")

        # Compute composite risk score
        risk_score = self.compute_blended_score(text_result, url_result)

        # Confidence is the normalized 0.00-1.00 risk index
        confidence = round(risk_score / 100.0, 2)

        # Map to 3-state verdict
        verdict = self.determine_verdict(risk_score)

        # Evidence bullet points
        evidence = self.synthesize_evidence(verdict, risk_score, text_result, url_result)

        # Contextual summary & advice
        summary = self.generate_summary(verdict, risk_score, has_text, has_url)
        recommended_action = self.generate_recommended_action(verdict)

        # Serialized modalities
        text_payload = text_result.to_dict() if has_text else {"provided": False}
        url_payload = url_result.to_dict() if has_url else {"provided": False}

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return UnifiedVerdict(
            verdict=verdict,
            risk_score=risk_score,
            confidence=confidence,
            summary=summary,
            text_analysis=text_payload,
            url_analysis=url_payload,
            evidence=evidence,
            recommended_action=recommended_action,
            analyzed_at=now_utc,
        )


# Singleton arbiter instance
verdict_arbiter = VerdictArbiter()


def synthesize_verdict(
    text_result: Optional[TextAnalysisResult] = None,
    url_result: Optional[URLAnalysisResult] = None,
) -> UnifiedVerdict:
    """Convenience functional interface for the singleton VerdictArbiter."""
    return verdict_arbiter.synthesize(text_result, url_result)
