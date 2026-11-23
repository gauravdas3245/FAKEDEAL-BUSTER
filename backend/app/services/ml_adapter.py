from pathlib import Path
from typing import Any, Dict, Optional

from app.exceptions import MLServiceUnavailableError
from ml.service import MLService, load_ml_service


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIRECTORY = REPOSITORY_ROOT / "artifacts" / "ml" / "isolation_forest_v1"


class CentralMLAdapter:
    """Lazily load and delegate to the verified central ML application service."""

    def __init__(self, service: Optional[MLService] = None, artifact_dir: Path = ARTIFACT_DIRECTORY):
        self._service = service
        self.artifact_dir = Path(artifact_dir)

    def analyze(self, **observation: Any) -> Dict[str, Any]:
        if self._service is None:
            try:
                self._service = load_ml_service(self.artifact_dir)
            except Exception as exc:
                raise MLServiceUnavailableError(
                    "The verified ML artifact bundle could not be loaded."
                ) from exc
        try:
            result = self._service.analyze_product_observation(**observation)
        except Exception as exc:
            raise RuntimeError("Central ML analysis raised an unexpected error.") from exc

        status = result.get("status")
        if status == "INVALID_INPUT":
            detail = result.get("error") or {}
            raise ValueError(detail.get("message", "The central ML service rejected the input."))
        if status == "PROCESSING_ERROR":
            detail = result.get("error") or {}
            raise RuntimeError(detail.get("message", "Central ML processing failed."))
        if status not in {"OK", "NEEDS_MORE_DATA"}:
            raise RuntimeError(f"Central ML service returned unsupported status: {status!r}")
        return result
