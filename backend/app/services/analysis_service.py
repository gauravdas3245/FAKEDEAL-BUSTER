from typing import Optional

from app.schemas.request import AnalyzeRequest
from app.schemas.response import AnalyzeResponse
from app.services.history_service import HistoryService
from app.services.ml_adapter import CentralMLAdapter
from app.services.synthetic_classifier_adapter import SyntheticScenarioAdapter


class AnalysisService:
    def __init__(self, history_service: Optional[HistoryService] = None,
                 ml_adapter: Optional[CentralMLAdapter] = None,
                 synthetic_classifier: Optional[SyntheticScenarioAdapter] = None):
        self.history_service = history_service or HistoryService()
        self.ml_adapter = ml_adapter or CentralMLAdapter()
        self.synthetic_classifier = synthetic_classifier or SyntheticScenarioAdapter()

    def analyze(self, request: AnalyzeRequest, category: str | None = None) -> AnalyzeResponse:
        product_id = request.product_id.strip().upper()
        platform = request.platform.strip().lower()
        history = self.history_service.lookup_history(product_id, platform, request.as_of)

        result = self.ml_adapter.analyze(
            product_id=product_id,
            platform=platform,
            timestamp=request.as_of,
            current_price=request.current_price,
            original_price=request.original_price,
            historical_observations=history,
        )
        anomaly = result["ml_anomaly"]
        fdi = result["fdi"]
        synthetic_classifier = self.synthetic_classifier.classify(
            anomaly, current_price=request.current_price, original_price=request.original_price,
            platform=platform, category=category,
        )
        state = result["status"]
        if state == "NEEDS_MORE_DATA" or (isinstance(anomaly, dict) and anomaly.get("status") == "NEEDS_MORE_DATA"):
            explanation = anomaly.get("explanation", {}).get("message", "Insufficient historical price data.") if isinstance(anomaly, dict) else "Insufficient historical price data."
            assessment_verdict = "Insufficient Evidence"
            assessment_explanation = (
                "Insufficient historical price observations (at least 14 days required) exist to establish a baseline."
            )
        elif isinstance(anomaly, dict) and anomaly.get("verdict") == "ANOMALY":
            explanation = anomaly.get("explanation", {}).get("interpretation", "Price anomaly detected.")
            assessment_verdict = "Potential Suspicious Discount Pattern"
            assessment_explanation = (
                "The Isolation Forest anomaly detector identified an unusual pricing or discount pattern relative to "
                "the product's 30-day historical baseline. This indicates a statistical anomaly, not confirmed fraud."
            )
        elif isinstance(anomaly, dict) and anomaly.get("verdict") == "NO_ANOMALY":
            explanation = anomaly.get("explanation", {}).get("interpretation", "No price anomaly detected.")
            assessment_verdict = "No Suspicious Pattern Detected"
            assessment_explanation = (
                "The listed price and reference discount are consistent with typical historical price patterns observed "
                "for this product within normal variance."
            )
        else:
            explanation = "Analysis could not produce a conclusive result."
            assessment_verdict = "Insufficient Evidence"
            assessment_explanation = "Model or data inputs were insufficient to produce an assessment."

        if isinstance(fdi, dict) and fdi.get("status") == "INSUFFICIENT_INPUTS":
            explanation += " FDI score and risk level are unavailable because required FDI inputs are missing."

        discount = round((request.original_price - request.current_price) / request.original_price * 100, 2)
        return AnalyzeResponse(
            success=True,
            analysis_status=state,
            verdict=fdi.get("provisional_level") if isinstance(fdi, dict) and fdi.get("status") == "OK" else None,
            fdi_score=fdi.get("fdi_score") if isinstance(fdi, dict) and fdi.get("status") == "OK" else None,
            confidence=None,
            explanation=explanation,
            original_price=request.original_price,
            current_price=request.current_price,
            discount_percentage=discount,
            forecast_status="UNAVAILABLE",
            forecast=None,
            ml_anomaly=anomaly,
            fdi=fdi,
            synthetic_classifier=synthetic_classifier,
            assessment_verdict=assessment_verdict,
            assessment_explanation=assessment_explanation,
        )
