from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    success: bool = True
    analysis_status: str
    verdict: Optional[str] = None
    fdi_score: Optional[float] = None
    confidence: Optional[float] = None
    explanation: str
    original_price: float
    current_price: float
    discount_percentage: float
    forecast_status: str = "UNAVAILABLE"
    forecast: None = None
    ml_anomaly: Optional[Dict[str, Any]] = Field(
        description="The unmodified central ML inference result; not a fraud classification."
    )
    fdi: Optional[Dict[str, Any]] = Field(
        description="The central FDI result, including INSUFFICIENT_INPUTS when applicable."
    )
    synthetic_classifier: Optional[Dict[str, Any]] = Field(
        default=None,
        description="A separately trained classifier for resemblance to generated scenarios only; not a fraud prediction.",
    )
    assessment_verdict: Optional[str] = Field(
        default=None,
        description="Standardized assessment state: Potential Suspicious Discount Pattern, No Suspicious Pattern Detected, or Insufficient Evidence.",
    )
    assessment_explanation: Optional[str] = Field(
        default=None,
        description="Clear description of the assessment verdict.",
    )


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
