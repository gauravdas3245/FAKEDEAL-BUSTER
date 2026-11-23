import hashlib
import math
from pathlib import Path

import pytest

from ml.fdi import (
    COMPONENT_WEIGHTS,
    METHODOLOGY_VERSION,
    REQUIRED_INPUTS,
    VALIDATION_STATUS,
    calculate_fdi,
    calculate_fdi_from_inference,
    score_anomaly,
    score_discount_gap,
    score_mean_ratio,
    score_msrp_inflation,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/ml/isolation_forest_v1"


def full_inputs(score=50):
    return {
        "discount_pct": score / 2,
        "real_discount_30d": 0,
        "ratio_to_30d_avg": 0.85 + 0.30 * score / 100,
        "msrp_inflation_ratio": 1 + 0.25 * score / 100,
        "price_spike_flag": 0,
        "pre_discount_hike_ratio": score / 200,
    }


@pytest.mark.parametrize("claim,real,expected", [
    (0, 0, 0), (25, 0, 50), (50, 0, 100), (100, 0, 100), (10, 20, 0),
])
def test_discount_gap_formula_and_clipping(claim, real, expected):
    assert score_discount_gap(claim, real) == pytest.approx(expected)


@pytest.mark.parametrize("ratio,expected", [
    (0.0, 0), (0.85, 0), (1.0, 50), (1.15, 100), (2.0, 100),
])
def test_mean_ratio_formula_and_clipping(ratio, expected):
    assert score_mean_ratio(ratio) == pytest.approx(expected)


@pytest.mark.parametrize("ratio,expected", [
    (0.0, 0), (1.0, 0), (1.125, 50), (1.25, 100), (3.0, 100),
])
def test_msrp_inflation_formula_and_clipping(ratio, expected):
    assert score_msrp_inflation(ratio) == pytest.approx(expected)


@pytest.mark.parametrize("flag,hike,expected", [
    (0, 0, 0), (1, 0, 60), (0, 0.10, 20), (1, 0.20, 100), (1, 1, 100),
])
def test_anomaly_component_formula_and_clipping(flag, hike, expected):
    assert score_anomaly(flag, hike) == pytest.approx(expected)


@pytest.mark.parametrize("value,level", [(0, "LOW"), (29.999, "LOW"), (30, "MODERATE"),
                                          (59.999, "MODERATE"), (60, "HIGH"),
                                          (79.999, "HIGH"), (80, "CRITICAL"), (100, "CRITICAL")])
def test_weighted_total_and_level_boundaries(value, level):
    result = calculate_fdi(full_inputs(value))
    assert result["status"] == "OK"
    assert result["fdi_score"] == pytest.approx(value)
    assert result["provisional_level"] == level
    assert sum(result["component_weights"].values()) == 1.0
    assert result["validation_status"] == "PROVISIONAL_NOT_VALIDATED"
    assert result["methodology_version"] == METHODOLOGY_VERSION


def test_partial_signals_show_components_but_never_weight_partial_total():
    inputs = full_inputs()
    inputs["price_spike_flag"] = None
    inputs["pre_discount_hike_ratio"] = None
    result = calculate_fdi(inputs)
    assert result["status"] == "INSUFFICIENT_INPUTS"
    assert result["fdi_score"] is result["provisional_level"] is None
    assert result["component_scores"]["S_gap"] is not None
    assert result["component_scores"]["S_mean_ratio"] is not None
    assert result["component_scores"]["S_msrp_inflation"] is not None
    assert result["component_scores"]["S_anomaly"] is None
    assert result["missing_inputs"] == ["price_spike_flag", "pre_discount_hike_ratio"]


def test_absent_required_component_makes_fdi_unavailable():
    inputs = full_inputs()
    for name in REQUIRED_INPUTS:
        case = dict(inputs)
        case.pop(name)
        result = calculate_fdi(case)
        assert result["fdi_score"] is None
        assert name in result["missing_inputs"]


@pytest.mark.parametrize("fn,args", [
    (score_discount_gap, (-1, 0)), (score_discount_gap, (101, 0)),
    (score_mean_ratio, (-0.1,)), (score_msrp_inflation, (-1,)),
    (score_anomaly, (-1, 0)), (score_anomaly, (2, 0)), (score_anomaly, (0, -0.1)),
])
def test_negative_and_out_of_range_inputs_rejected(fn, args):
    with pytest.raises(ValueError):
        fn(*args)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values_rejected(bad):
    with pytest.raises(ValueError):
        score_mean_ratio(bad)
    with pytest.raises(ValueError):
        score_discount_gap(10, bad)


def test_missing_none_is_unavailable_but_null_numeric_is_not_silently_scored():
    case = full_inputs()
    case["pre_discount_hike_ratio"] = None
    assert calculate_fdi(case)["fdi_score"] is None
    case["pre_discount_hike_ratio"] = math.nan
    with pytest.raises(ValueError, match="finite"):
        calculate_fdi(case)


def test_inference_adapter_derives_only_verified_inputs_and_does_not_use_if_score():
    inference = {"status": "OK", "anomaly_score": 999999,
                 "features": {"ratio_to_30d_avg": 0.8, "msrp_to_30d_avg": 1.5}}
    result = calculate_fdi_from_inference(inference, current_price=80, original_price=150)
    assert result["status"] == "INSUFFICIENT_INPUTS"
    assert result["fdi_score"] is None
    assert result["component_scores"]["S_gap"] is not None
    assert result["component_scores"]["S_mean_ratio"] == 0
    assert result["component_scores"]["S_msrp_inflation"] == 100
    assert result["component_scores"]["S_anomaly"] is None
    assert result["missing_inputs"] == ["price_spike_flag", "pre_discount_hike_ratio"]


def test_anomaly_or_missing_inference_does_not_invent_history_components():
    result = calculate_fdi_from_inference(
        {"status": "NEEDS_MORE_DATA", "features": None, "anomaly_score": 0.8},
        current_price=80, original_price=100,
    )
    assert result["fdi_score"] is None
    assert {"ratio_to_30d_avg", "msrp_inflation_ratio", "real_discount_30d"}.issubset(result["missing_inputs"])


def test_no_target_label_or_isolation_forest_input_substitution_in_fdi_source():
    source = (ROOT / "ml/fdi.py").read_text(encoding="utf-8")
    assert "fake_discount_flag" not in source
    assert "anomaly_score" not in source


def test_determinism_and_provisional_status_always_present():
    inputs = full_inputs(64.5)
    first = calculate_fdi(inputs)
    second = calculate_fdi(inputs)
    assert first == second
    assert first["validation_status"] == VALIDATION_STATUS
    assert calculate_fdi({})["validation_status"] == VALIDATION_STATUS


def test_v1_artifact_manifest_hashes_still_match():
    for line in (ARTIFACT_DIR / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", 1)
        digest = hashlib.sha256((ARTIFACT_DIR / filename).read_bytes()).hexdigest()
        assert digest == expected
