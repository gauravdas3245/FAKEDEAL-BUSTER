"""Reusable, artifact-verified inference for the saved FakeDeal Buster model."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from ml.feature_extractor import FEATURE_NAMES, MINIMUM_HISTORICAL_DAYS
from ml.isolation_forest import IsolationForestDetector
from ml.preprocessor import FeaturePreprocessor


class InferenceValidationError(ValueError):
    """Raised when an observation or its history violates the inference contract."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise InferenceValidationError(f"timestamp must be ISO-8601: {value!r}") from exc
        # Dataset timestamps are timezone-naive. Normalize aware values to UTC-naive.
        return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed
    raise InferenceValidationError("timestamp must be a date, datetime, or ISO-8601 string")


class InferenceEngine:
    """Load artifacts once and reuse them for individual or bounded batch predictions."""

    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir.resolve()
        manifest_path = self.artifact_dir / "checksums.sha256"
        if not manifest_path.is_file():
            raise ValueError(f"Artifact checksum manifest is missing: {manifest_path}")
        entries = {}
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            try:
                expected, filename = line.split("  ", 1)
            except ValueError as exc:
                raise ValueError("Malformed artifact checksum manifest") from exc
            if Path(filename).name != filename:
                raise ValueError(f"Unsafe artifact filename in checksum manifest: {filename}")
            entries[filename] = expected
        required = {"isolation_forest.joblib", "preprocessor.json", "metadata.json"}
        if not required.issubset(entries):
            raise ValueError(f"Checksum manifest does not cover required artifacts: {sorted(required - entries.keys())}")
        for filename, expected in entries.items():
            file_path = self.artifact_dir / filename
            if not file_path.is_file() or _sha256(file_path) != expected:
                raise ValueError(f"Artifact checksum verification failed: {filename}")

        self.metadata = json.loads((self.artifact_dir / "metadata.json").read_text(encoding="utf-8"))
        self.model_version = self.metadata.get("artifact_version")
        if not self.model_version:
            raise ValueError("Artifact metadata has no artifact_version")
        if self.metadata.get("feature_names") != list(FEATURE_NAMES):
            raise ValueError("Artifact metadata feature order does not match the inference feature contract")
        self.preprocessor = FeaturePreprocessor.load_json(self.artifact_dir / "preprocessor.json")
        if not self.preprocessor.is_fitted or self.preprocessor.feature_names != list(FEATURE_NAMES):
            raise ValueError("Saved preprocessor is unfitted or has an incompatible feature order")
        if self.preprocessor.scaler_type != self.metadata.get("preprocessing", {}).get("type"):
            raise ValueError("Preprocessor type does not match artifact metadata")
        self.detector = IsolationForestDetector.load(self.artifact_dir / "isolation_forest.joblib")
        if not self.detector.is_fitted or self.detector.feature_names != list(FEATURE_NAMES):
            raise ValueError("Saved detector is unfitted or has an incompatible feature order")
        self.minimum_history = int(self.metadata.get("historical_window", {}).get(
            "minimum_prior_observations", MINIMUM_HISTORICAL_DAYS
        ))

    def predict_product_observation(
        self,
        *,
        product_id: str,
        platform: str,
        timestamp: Any,
        current_price: Any,
        original_price: Any,
        historical_observations: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """Score a listing against prior prices for the exact product/platform key."""
        if not isinstance(product_id, str) or not product_id.strip():
            raise InferenceValidationError("product_id must be a non-empty string")
        if not isinstance(platform, str) or not platform.strip():
            raise InferenceValidationError("platform must be a non-empty string")
        when = _parse_timestamp(timestamp)
        current = _valid_price(current_price, "current_price")
        original = _valid_price(original_price, "original_price")
        if original < current:
            raise InferenceValidationError("original_price cannot be less than current_price")
        if not isinstance(historical_observations, Sequence) or isinstance(historical_observations, (str, bytes)):
            raise InferenceValidationError("historical_observations must be a sequence of records")

        history: List[Dict[str, Any]] = []
        seen_timestamps: Dict[datetime, float] = {}
        for index, record in enumerate(historical_observations):
            if not isinstance(record, Mapping):
                raise InferenceValidationError(f"Historical observation {index} must be a mapping")
            if "product_id" not in record or "platform" not in record:
                raise InferenceValidationError(f"Historical observation {index} requires product_id and platform")
            if record["product_id"] != product_id or record["platform"] != platform:
                raise InferenceValidationError(
                    f"Historical observation {index} key does not match ({product_id!r}, {platform!r})"
                )
            if "timestamp" not in record and "date" not in record:
                raise InferenceValidationError(f"Historical observation {index} requires timestamp")
            if "price" not in record:
                raise InferenceValidationError(f"Historical observation {index} requires price")
            price = _valid_price(record["price"], f"historical_observations[{index}].price")
            historical_when = _parse_timestamp(record.get("timestamp", record.get("date")))
            if historical_when in seen_timestamps:
                if seen_timestamps[historical_when] != price:
                    raise InferenceValidationError(
                        f"Duplicate conflicting historical prices at timestamp {historical_when.isoformat()}"
                    )
                continue
            seen_timestamps[historical_when] = price
            history.append({"timestamp": historical_when, "price": price})

        # Match the training SQL RANGE convention exactly: inclusive lower bound,
        # exclusive current timestamp, partitioned by the validated product/platform key.
        prior_30 = [item for item in history if when - timedelta(days=30) <= item["timestamp"] < when]
        prior_7 = [item for item in history if when - timedelta(days=7) <= item["timestamp"] < when]
        observed_30_days = {item["timestamp"].date() for item in prior_30}
        if len(observed_30_days) < self.minimum_history or not prior_7:
            return {
                "status": "NEEDS_MORE_DATA", "product_id": product_id, "platform": platform,
                "timestamp": when.isoformat(sep=" "), "verdict": None, "anomaly_score": None,
                "is_anomaly": None, "features": None,
                "explanation": {"reason": "INSUFFICIENT_HISTORY",
                                "message": "Insufficient historical price data to analyse this product."},
                "model_version": self.model_version,
            }

        prices_30 = [item["price"] for item in prior_30]
        mean_30 = sum(prices_30) / len(prices_30)
        if not math.isfinite(mean_30) or mean_30 <= 0:
            raise InferenceValidationError("Historical 30-day mean is invalid")
        variance = sum((value - mean_30) ** 2 for value in prices_30) / (len(prices_30) - 1)
        std_30 = math.sqrt(variance)
        max_7 = max(item["price"] for item in prior_7)
        features = {
            "msrp_to_30d_avg": original / mean_30,
            "ratio_to_30d_avg": current / mean_30,
            "price_volatility_30d": std_30 / mean_30,
            "recent_7d_surge": max(0.0, (max_7 - mean_30) / mean_30),
        }
        if not all(math.isfinite(value) for value in features.values()):
            raise InferenceValidationError("Calculated features contain non-finite values")
        scaled = self.preprocessor.transform_single(features)
        prediction = self.detector.predict_anomaly(scaled)
        is_anomaly = bool(prediction["is_anomaly"])
        explanations = {
            "model_result": "Isolation Forest flagged an unusual feature combination." if is_anomaly else
                            "Isolation Forest did not flag an unusual feature combination.",
            "feature_descriptions": {
                "msrp_to_30d_avg": f"Original price is {features['msrp_to_30d_avg']:.3f}x the prior 30-day average.",
                "ratio_to_30d_avg": f"Current price is {features['ratio_to_30d_avg']:.3f}x the prior 30-day average.",
                "price_volatility_30d": f"Prior 30-day sample volatility is {features['price_volatility_30d']:.3f} of the average.",
                "recent_7d_surge": f"Recent 7-day maximum is {features['recent_7d_surge']:.3f} above the prior 30-day average (floored at zero).",
            },
            "reference_values": {"prior_30d_mean_price": mean_30,
                                 "prior_30d_observation_count": len(prior_30),
                                 "prior_7d_observation_count": len(prior_7)},
            "interpretation": "Feature descriptions are descriptive, not causal model attributions. An anomaly is not proof of fraud.",
        }
        return {
            "status": "OK", "product_id": product_id, "platform": platform,
            "timestamp": when.isoformat(sep=" "),
            "verdict": "ANOMALY" if is_anomaly else "NO_ANOMALY",
            "anomaly_score": float(prediction["anomaly_score"]), "is_anomaly": is_anomaly,
            "features": {name: float(features[name]) for name in FEATURE_NAMES},
            "explanation": explanations, "model_version": self.model_version,
        }

    def predict_batch(self, observations: Iterable[Mapping[str, Any]], *, batch_size: int = 256) -> List[Dict[str, Any]]:
        """Convenience list wrapper; use iter_predict_batch for very large streams."""
        return list(self.iter_predict_batch(observations, batch_size=batch_size))

    def iter_predict_batch(self, observations: Iterable[Mapping[str, Any]], *, batch_size: int = 256):
        """Yield results from bounded groups without retaining the full result set."""
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        batch: List[Mapping[str, Any]] = []
        for observation in observations:
            if not isinstance(observation, Mapping):
                raise InferenceValidationError("Each batch observation must be a mapping")
            batch.append(observation)
            if len(batch) == batch_size:
                yield from self._predict_independent(batch)
                batch.clear()
        if batch:
            yield from self._predict_independent(batch)

    def _predict_independent(self, batch: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for item in batch:
            try:
                results.append(self.predict_product_observation(**item))
            except InferenceValidationError as exc:
                # Keep a per-item validation error from affecting its neighbors.
                results.append({"status": "INVALID_INPUT", "product_id": item.get("product_id"),
                                "platform": item.get("platform"), "verdict": None,
                                "anomaly_score": None, "is_anomaly": None, "features": None,
                                "explanation": {"reason": "VALIDATION_ERROR", "message": str(exc)},
                                "model_version": self.model_version})
        return results


def _valid_price(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise InferenceValidationError(f"{name} must be a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InferenceValidationError(f"{name} must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0:
        raise InferenceValidationError(f"{name} must be a positive finite number")
    return number


def load_inference_engine(artifact_dir: str | Path) -> InferenceEngine:
    """Verify and load an inference engine once for application reuse."""
    return InferenceEngine(Path(artifact_dir))


def predict_product_observation(engine: InferenceEngine, **observation: Any) -> Dict[str, Any]:
    return engine.predict_product_observation(**observation)


def predict_batch(engine: InferenceEngine, observations: Iterable[Mapping[str, Any]], *, batch_size: int = 256) -> List[Dict[str, Any]]:
    return engine.predict_batch(observations, batch_size=batch_size)
