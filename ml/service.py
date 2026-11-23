"""Stable application-facing orchestration for inference and provisional FDI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from ml.fdi import METHODOLOGY_VERSION, calculate_fdi_from_inference
from ml.inference import InferenceEngine, InferenceValidationError, load_inference_engine


class MLService:
    """Owns one reusable inference engine and keeps ML and FDI results separate."""

    def __init__(self, inference_engine: InferenceEngine):
        self.inference_engine = inference_engine

    @property
    def model_version(self) -> str:
        return self.inference_engine.model_version

    def analyze_product_observation(
        self,
        *,
        product_id: str,
        platform: str,
        timestamp: Any,
        current_price: Any,
        original_price: Any,
        historical_observations: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """Run historical inference and available FDI diagnostics for one listing.

        Validation and processing failures return null model/FDI results. No score,
        verdict, or confidence value is synthesized on an error path.
        """
        try:
            inference = self.inference_engine.predict_product_observation(
                product_id=product_id,
                platform=platform,
                timestamp=timestamp,
                current_price=current_price,
                original_price=original_price,
                historical_observations=historical_observations,
            )
            fdi = calculate_fdi_from_inference(
                inference,
                current_price=current_price,
                original_price=original_price,
            )
        except InferenceValidationError as exc:
            return self._error("INVALID_INPUT", "VALIDATION_ERROR", str(exc))
        except ValueError as exc:
            # FDI validates its own derived inputs as well. Treat malformed data as
            # input failure, while preserving the absence of all prediction claims.
            return self._error("INVALID_INPUT", "VALIDATION_ERROR", str(exc))
        except Exception:
            # Avoid returning partial model results if any orchestration step fails.
            return self._error(
                "PROCESSING_ERROR",
                "ANALYSIS_FAILED",
                "ML analysis could not be completed.",
            )

        status = "NEEDS_MORE_DATA" if inference.get("status") == "NEEDS_MORE_DATA" else "OK"
        return {
            "status": status,
            "ml_anomaly": inference,
            "fdi": fdi,
            "model_version": self.model_version,
            "methodology_version": METHODOLOGY_VERSION,
        }

    def _error(self, status: str, code: str, message: str) -> Dict[str, Any]:
        return {
            "status": status,
            "ml_anomaly": None,
            "fdi": None,
            "error": {"code": code, "message": message},
            "model_version": self.model_version,
            "methodology_version": METHODOLOGY_VERSION,
        }


def load_ml_service(artifact_dir: Optional[str | Path] = None) -> MLService:
    """Load and verify v1 artifacts once; reuse the returned service per process."""
    path = Path(artifact_dir) if artifact_dir is not None else (
        Path(__file__).resolve().parents[1] / "artifacts" / "ml" / "isolation_forest_v1"
    )
    return MLService(load_inference_engine(path))
