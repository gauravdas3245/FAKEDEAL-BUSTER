"""Provisional Fake Discount Index heuristics, kept separate from model features."""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional


METHODOLOGY_VERSION = "fdi_provisional_v1"
VALIDATION_STATUS = "PROVISIONAL_NOT_VALIDATED"
COMPONENT_WEIGHTS = MappingProxyType({
    "S_gap": 0.35,
    "S_mean_ratio": 0.30,
    "S_msrp_inflation": 0.20,
    "S_anomaly": 0.15,
})
REQUIRED_INPUTS = (
    "discount_pct",
    "real_discount_30d",
    "ratio_to_30d_avg",
    "msrp_inflation_ratio",
    "price_spike_flag",
    "pre_discount_hike_ratio",
)


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite numeric value")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite numeric value") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{name} must be finite")
    return parsed


def _unit_percent(value: float, denominator: float) -> float:
    return min(1.0, max(0.0, value / denominator)) * 100.0


def score_discount_gap(discount_pct: float, real_discount_30d: float) -> float:
    """Score claimed-vs-history discount gap; real discount may be negative."""
    claim = _number(discount_pct, "discount_pct")
    real = _number(real_discount_30d, "real_discount_30d")
    if not 0.0 <= claim <= 100.0:
        raise ValueError("discount_pct must be within [0, 100]")
    return _unit_percent(claim - real, 50.0)


def score_mean_ratio(ratio_to_30d_avg: float) -> float:
    ratio = _number(ratio_to_30d_avg, "ratio_to_30d_avg")
    if ratio < 0:
        raise ValueError("ratio_to_30d_avg cannot be negative")
    return min(100.0, max(0.0, (ratio - 0.85) / 0.30 * 100.0))


def score_msrp_inflation(msrp_inflation_ratio: float) -> float:
    ratio = _number(msrp_inflation_ratio, "msrp_inflation_ratio")
    if ratio < 0:
        raise ValueError("msrp_inflation_ratio cannot be negative")
    return min(100.0, max(0.0, (ratio - 1.0) / 0.25 * 100.0))


def score_anomaly(price_spike_flag: float, pre_discount_hike_ratio: float) -> float:
    flag = _number(price_spike_flag, "price_spike_flag")
    hike = _number(pre_discount_hike_ratio, "pre_discount_hike_ratio")
    if flag not in (0.0, 1.0):
        raise ValueError("price_spike_flag must be exactly 0 or 1")
    if hike < 0:
        raise ValueError("pre_discount_hike_ratio cannot be negative")
    return min(100.0, max(0.0, 0.6 * (flag * 100.0) + 0.4 * (hike / 0.20 * 100.0)))


def _level(score: float) -> str:
    if score < 30:
        return "LOW"
    if score < 60:
        return "MODERATE"
    if score < 80:
        return "HIGH"
    return "CRITICAL"


def calculate_fdi(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    """Compute all proposed components; never returns a partial weighted FDI.

    Missing (`None`) signals keep independently calculable components visible but
    set the official total and level to null with `INSUFFICIENT_INPUTS` status.
    """
    if not isinstance(inputs, Mapping):
        raise ValueError("inputs must be a mapping")
    missing = [name for name in REQUIRED_INPUTS if name not in inputs or inputs[name] is None]
    scores: Dict[str, Optional[float]] = {
        "S_gap": None,
        "S_mean_ratio": None,
        "S_msrp_inflation": None,
        "S_anomaly": None,
    }
    component_inputs = {
        "S_gap": ("discount_pct", "real_discount_30d"),
        "S_mean_ratio": ("ratio_to_30d_avg",),
        "S_msrp_inflation": ("msrp_inflation_ratio",),
        "S_anomaly": ("price_spike_flag", "pre_discount_hike_ratio"),
    }
    functions = {
        "S_gap": lambda: score_discount_gap(inputs["discount_pct"], inputs["real_discount_30d"]),
        "S_mean_ratio": lambda: score_mean_ratio(inputs["ratio_to_30d_avg"]),
        "S_msrp_inflation": lambda: score_msrp_inflation(inputs["msrp_inflation_ratio"]),
        "S_anomaly": lambda: score_anomaly(inputs["price_spike_flag"], inputs["pre_discount_hike_ratio"]),
    }
    for component, names in component_inputs.items():
        if all(name in inputs and inputs[name] is not None for name in names):
            scores[component] = float(functions[component]())

    status = "INSUFFICIENT_INPUTS" if missing else "OK"
    total: Optional[float] = None
    level: Optional[str] = None
    if not missing:
        # Remove only floating-point representation noise so exact proposed band
        # boundaries (30, 60, 80) remain stable and deterministic.
        total = round(sum(COMPONENT_WEIGHTS[key] * float(scores[key]) for key in COMPONENT_WEIGHTS), 12)
        total = min(100.0, max(0.0, total))
        level = _level(total)

    return {
        "status": status,
        "fdi_score": total,
        "provisional_level": level,
        "component_scores": scores,
        "component_weights": dict(COMPONENT_WEIGHTS),
        "missing_inputs": missing,
        "explanation": {
            "summary": (
                "Provisional heuristic pricing index; not a fraud probability or proof."
                if total is not None else
                "FDI total unavailable because required pricing signals are missing; visible component scores are partial diagnostics only."
            ),
            "components": {
                "S_gap": "Difference between claimed discount percentage and the current discount versus prior 30-day mean.",
                "S_mean_ratio": "Current price relative to prior 30-day mean.",
                "S_msrp_inflation": "Advertised original price relative to prior 30-day mean.",
                "S_anomaly": "Proposed combination of a price-spike flag and pre-discount hike ratio; unavailable unless both signals are independently supplied.",
            },
            "status_note": VALIDATION_STATUS,
        },
        "methodology_version": METHODOLOGY_VERSION,
        "validation_status": VALIDATION_STATUS,
    }


def calculate_fdi_from_inference(
    inference_result: Mapping[str, Any],
    *,
    current_price: Any,
    original_price: Any,
    price_spike_flag: Any = None,
    pre_discount_hike_ratio: Any = None,
) -> Dict[str, Any]:
    """Derive reproducible inputs from inference output and mark unavailable signals.

    The two optional anomaly signals are not derivable from the current verified
    inference contract. Callers must not copy dataset-only labels into these slots.
    """
    if not isinstance(inference_result, Mapping):
        raise ValueError("inference_result must be a mapping")
    current = _number(current_price, "current_price")
    original = _number(original_price, "original_price")
    if current <= 0 or original <= 0:
        raise ValueError("current_price and original_price must be positive")
    features = inference_result.get("features")
    inputs: Dict[str, Any] = {
        "discount_pct": ((original - current) / original) * 100.0,
        "price_spike_flag": price_spike_flag,
        "pre_discount_hike_ratio": pre_discount_hike_ratio,
    }
    if inference_result.get("status") == "OK" and isinstance(features, Mapping):
        ratio = features.get("ratio_to_30d_avg")
        inputs["ratio_to_30d_avg"] = ratio
        inputs["msrp_inflation_ratio"] = features.get("msrp_to_30d_avg")
        if ratio is not None:
            ratio_value = _number(ratio, "ratio_to_30d_avg")
            inputs["real_discount_30d"] = (1.0 - ratio_value) * 100.0
    else:
        inputs["ratio_to_30d_avg"] = None
        inputs["msrp_inflation_ratio"] = None
        inputs["real_discount_30d"] = None
    return calculate_fdi(inputs)
