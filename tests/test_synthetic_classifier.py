import numpy as np
import pandas as pd
import pytest

from ml.synthetic_classifier import (classify_synthetic_scenario, load_classifier_bundle,
                                     train_classifier_suite)
from ml.synthetic_discount import (FEATURE_NAMES, NUMERIC_FEATURES, TARGET_COLUMN,
                                   generate_synthetic_scenarios, split_synthetic_scenarios)


def reference_profiles(count=1800):
    rng = np.random.default_rng(17)
    ratio = rng.uniform(0.55, 1.15, count)
    msrp = ratio / rng.uniform(0.12, 0.70, count)
    return pd.DataFrame({
        "platform": rng.choice(["amazon", "ebay", "walmart"], count),
        "category": rng.choice(["Electronics", "Fashion", "Books"], count),
        "msrp_to_30d_avg": msrp,
        "ratio_to_30d_avg": ratio,
        "price_volatility_30d": rng.uniform(0.01, 0.25, count),
        "recent_7d_surge": rng.uniform(0, 0.4, count),
        "advertised_discount_pct": np.clip((1 - ratio / msrp) * 100, 3, 75),
    })


def test_synthetic_generation_is_reproducible_and_target_is_not_a_feature():
    profiles = reference_profiles()
    first = generate_synthetic_scenarios(profiles, row_count=600, seed=21)
    second = generate_synthetic_scenarios(profiles, row_count=600, seed=21)
    pd.testing.assert_frame_equal(first, second)
    assert first[TARGET_COLUMN].value_counts().to_dict() == {0: 300, 1: 300}
    assert set(FEATURE_NAMES).isdisjoint({TARGET_COLUMN, "scenario_name"})
    assert all(name in first for name in (*FEATURE_NAMES, TARGET_COLUMN))
    assert first[list(NUMERIC_FEATURES)].to_numpy().shape == (600, len(NUMERIC_FEATURES))


def test_split_sizes_are_stratified_and_preserve_both_synthetic_labels():
    data = generate_synthetic_scenarios(reference_profiles(), row_count=1000, seed=22)
    train, validation, test = split_synthetic_scenarios(data, seed=22)
    assert (len(train), len(validation), len(test)) == (700, 150, 150)
    for split in (train, validation, test):
        assert set(split[TARGET_COLUMN].unique()) == {0, 1}


def test_training_pipeline_serializes_both_models_and_verifies_bundle(tmp_path):
    data = generate_synthetic_scenarios(reference_profiles(), row_count=1200, seed=23)
    train, validation, test = split_synthetic_scenarios(data, seed=23)
    result = train_classifier_suite(train, validation, test, tmp_path / "models",
                                    seed=23, rf_estimators=15)
    metrics = result["evaluation"]["test_metrics"]
    assert set(metrics) == {"logistic_regression", "random_forest"}
    for scores in metrics.values():
        assert scores["support"] == {"synthetic_genuine": 90, "synthetic_artificially_inflated": 90}
        assert 0 <= scores["precision"] <= 1
        assert 0 <= scores["recall"] <= 1
        assert scores["roc_auc"] is not None
        assert scores["gini_coefficient_2auc_minus_1"] == pytest.approx(2 * scores["roc_auc"] - 1)
    bundle = load_classifier_bundle(tmp_path / "models")
    row = data.iloc[0]
    prediction = classify_synthetic_scenario(bundle, {name: row[name] for name in FEATURE_NAMES})
    assert prediction["status"] == "SYNTHETIC_SCENARIO_EXPERIMENT"
    assert "not a real-world fraud prediction" in prediction["disclaimer"]
    assert "fraud_probability" not in prediction


def test_classifier_bundle_rejects_modified_model_checksum(tmp_path):
    data = generate_synthetic_scenarios(reference_profiles(), row_count=600, seed=24)
    splits = split_synthetic_scenarios(data, seed=24)
    output = tmp_path / "models"
    train_classifier_suite(*splits, artifact_dir=output, seed=24, rf_estimators=5)
    with (output / "random_forest.joblib").open("ab") as stream:
        stream.write(b"corruption")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_classifier_bundle(output)
