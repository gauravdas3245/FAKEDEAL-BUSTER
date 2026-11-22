"""Synthetic-scenario LR/RF experiment, separate from production anomaly ML."""

from __future__ import annotations

import json
import platform as runtime_platform
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.synthetic_discount import (CATEGORICAL_FEATURES, FEATURE_NAMES, LABELS,
                                   NUMERIC_FEATURES, SYNTHETIC_VERSION, TARGET_COLUMN,
                                   sha256_file)


ARTIFACT_FILENAMES = {
    "logistic_regression": "logistic_regression.joblib",
    "random_forest": "random_forest.joblib",
}
FALSE_POSITIVE_RATE_LIMIT = 0.10


def _pipeline(kind: str, seed: int, rf_estimators: int) -> Pipeline:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if kind == "logistic_regression":
        numeric_steps.append(("scaler", StandardScaler()))
    preprocess = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline(numeric_steps), list(NUMERIC_FEATURES)),
            ("categorical", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]), list(CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
    )
    if kind == "logistic_regression":
        estimator = LogisticRegression(class_weight="balanced", max_iter=1500,
                                       solver="lbfgs", random_state=seed)
    elif kind == "random_forest":
        estimator = RandomForestClassifier(n_estimators=rf_estimators, max_depth=14,
                                            min_samples_leaf=2, max_features="sqrt",
                                            class_weight="balanced_subsample",
                                            n_jobs=-1, random_state=seed)
    else:
        raise ValueError(f"Unsupported classifier: {kind}")
    return Pipeline([("preprocessing", preprocess), ("classifier", estimator)])


def _validate_frame(frame: pd.DataFrame, split_name: str) -> None:
    required = {*FEATURE_NAMES, TARGET_COLUMN}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{split_name} split is missing columns: {sorted(missing)}")
    if set(frame[TARGET_COLUMN].dropna().unique()) != {0, 1}:
        raise ValueError(f"{split_name} split must contain both synthetic scenario labels")
    numeric = frame[list(NUMERIC_FEATURES)].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError(f"{split_name} split contains non-finite numeric features")


def _metrics(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    predicted = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(y_true, predicted, labels=[0, 1])
    auc = float(roc_auc_score(y_true, probabilities)) if len(np.unique(y_true)) == 2 else None
    average_precision = float(average_precision_score(y_true, probabilities)) if len(np.unique(y_true)) == 2 else None
    return {
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "roc_auc": auc,
        "pr_auc_average_precision": average_precision,
        "gini_coefficient_2auc_minus_1": 2.0 * auc - 1.0 if auc is not None else None,
        "false_positive_rate_on_synthetic_genuine": float(matrix[0, 1] / max(1, matrix[0].sum())),
        "confusion_matrix_labels_0_then_1": {"tn": int(matrix[0, 0]), "fp": int(matrix[0, 1]),
                                               "fn": int(matrix[1, 0]), "tp": int(matrix[1, 1])},
        "support": {"synthetic_genuine": int((y_true == 0).sum()),
                    "synthetic_artificially_inflated": int((y_true == 1).sum())},
    }


def _select_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> tuple[float, list[dict[str, float]]]:
    candidates = np.unique(np.concatenate([
        np.linspace(0.0, 1.0, 101),
        [float(np.nextafter(probabilities.max(), np.inf))],
    ]))
    sweep: list[dict[str, float]] = []
    for threshold in candidates:
        predicted = probabilities >= threshold
        positive = y_true == 1
        negative = ~positive
        tp = int(np.count_nonzero(predicted & positive))
        fp = int(np.count_nonzero(predicted & negative))
        fn = int(np.count_nonzero(~predicted & positive))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        sweep.append({"threshold": float(threshold), "precision": precision,
                      "recall": recall, "f1": f1,
                      "false_positive_rate": fp / max(1, int(negative.sum()))})
    eligible = [item for item in sweep if item["false_positive_rate"] <= FALSE_POSITIVE_RATE_LIMIT]
    selected = max(eligible, key=lambda item: (item["recall"], item["precision"], item["threshold"]))
    return selected["threshold"], sweep


def train_classifier_suite(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    artifact_dir: Path,
    *,
    seed: int = 20261118,
    rf_estimators: int = 300,
    dataset_manifest_sha256: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Fit preprocessing on train only and evaluate only once on held-out test."""
    for name, frame in (("train", train), ("validation", validation), ("test", test)):
        _validate_frame(frame, name)
    artifact_dir = Path(artifact_dir)
    if artifact_dir.exists() and any(artifact_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing classifier artifacts: {artifact_dir}")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    x_train, y_train = train[list(FEATURE_NAMES)], train[TARGET_COLUMN].astype(int).to_numpy()
    x_val, y_val = validation[list(FEATURE_NAMES)], validation[TARGET_COLUMN].astype(int).to_numpy()
    x_test, y_test = test[list(FEATURE_NAMES)], test[TARGET_COLUMN].astype(int).to_numpy()
    results: dict[str, Any] = {}
    pipelines: dict[str, Pipeline] = {}
    for name in ARTIFACT_FILENAMES:
        model = _pipeline(name, seed, rf_estimators)
        model.fit(x_train, y_train)
        transformed_names = model.named_steps["preprocessing"].get_feature_names_out()
        estimator = model.named_steps["classifier"]
        if hasattr(estimator, "feature_importances_"):
            importance_values = estimator.feature_importances_
        else:
            importance_values = np.mean(np.abs(estimator.coef_), axis=0)
        feature_importance = sorted(
            ({"feature": str(feature), "importance": float(value)}
             for feature, value in zip(transformed_names, importance_values)),
            key=lambda item: item["importance"], reverse=True,
        )
        validation_probability = model.predict_proba(x_val)[:, 1]
        threshold, sweep = _select_threshold(y_val, validation_probability)
        validation_metrics = _metrics(y_val, validation_probability, threshold)
        test_probability = model.predict_proba(x_test)[:, 1]
        test_metrics = _metrics(y_test, test_probability, threshold)
        pipelines[name] = model
        results[name] = {"validation": validation_metrics,
                         "test_synthetic_only": test_metrics,
                         "validation_threshold_sweep": sweep,
                         "transformed_feature_importance": feature_importance}

    # Choose using validation only: maximize recall subject to <=10% false-positive
    # rate on synthetic genuine examples, then use validation PR-AUC as tiebreaker.
    selected_name = max(
        ARTIFACT_FILENAMES,
        key=lambda name: (results[name]["validation"]["recall"],
                          results[name]["validation"]["pr_auc_average_precision"],
                          results[name]["validation"]["precision"]),
    )
    files = {}
    for name, filename in ARTIFACT_FILENAMES.items():
        path = artifact_dir / filename
        joblib.dump(pipelines[name], path, compress=3)
        files[filename] = sha256_file(path)
    metadata = {
        "artifact_version": "synthetic_discount_classifier_v1",
        "synthetic_only": True,
        "not_real_world_fraud_detection": True,
        "feature_names_ordered": list(FEATURE_NAMES),
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "target_column": TARGET_COLUMN,
        "labels": {str(key): value for key, value in LABELS.items()},
        "threshold_objective": "Validation recall maximized subject to false-positive rate <= 0.10 on synthetic genuine examples; PR-AUC and precision break ties.",
        "false_positive_rate_limit": FALSE_POSITIVE_RATE_LIMIT,
        "selected_model": selected_name,
        "selected_threshold": results[selected_name]["validation"]["threshold"],
        "transformed_feature_importance": {name: results[name]["transformed_feature_importance"] for name in ARTIFACT_FILENAMES},
        "split_counts": {"train": len(train), "validation": len(validation), "test": len(test)},
        "class_counts": {split: {str(k): int(v) for k, v in frame[TARGET_COLUMN].value_counts().sort_index().items()}
                         for split, frame in (("train", train), ("validation", validation), ("test", test))},
        "random_seed": seed,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "random_forest_estimators": rf_estimators,
        "fit_scope": "imputers, one-hot encoders, and scaler fitted only on synthetic training split",
        "training_environment": {"python": runtime_platform.python_version(), "scikit_learn": sklearn.__version__},
    }
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    evaluation = {
        "evaluation_scope": "SYNTHETIC_HELD_OUT_TEST_ONLY",
        "not_real_world_accuracy": True,
        "test_metrics": {name: results[name]["test_synthetic_only"] for name in ARTIFACT_FILENAMES},
        "validation_metrics": {name: results[name]["validation"] for name in ARTIFACT_FILENAMES},
        "validation_threshold_sweep": {name: results[name]["validation_threshold_sweep"] for name in ARTIFACT_FILENAMES},
        "selected_model": selected_name,
        "selected_model_test_metrics": results[selected_name]["test_synthetic_only"],
        "selection_basis": "validation split only; test split was not used for selection",
    }
    (artifact_dir / "evaluation.json").write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
    files["metadata.json"] = sha256_file(artifact_dir / "metadata.json")
    files["evaluation.json"] = sha256_file(artifact_dir / "evaluation.json")
    (artifact_dir / "checksums.sha256").write_text(
        "".join(f"{checksum}  {filename}\n" for filename, checksum in sorted(files.items())), encoding="utf-8")
    return {"metadata": metadata, "evaluation": evaluation}


def load_classifier_bundle(artifact_dir: Path) -> dict[str, Any]:
    artifact_dir = Path(artifact_dir)
    manifest = artifact_dir / "checksums.sha256"
    if not manifest.is_file():
        raise FileNotFoundError("Synthetic classifier checksum manifest is missing")
    expected = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        expected[filename] = digest
    required = {*ARTIFACT_FILENAMES.values(), "metadata.json", "evaluation.json"}
    if set(expected) != required:
        raise ValueError("Synthetic classifier bundle file list does not match the manifest")
    for filename, digest in expected.items():
        path = artifact_dir / filename
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"Synthetic classifier checksum mismatch: {filename}")
    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("feature_names_ordered") != list(FEATURE_NAMES) or not metadata.get("synthetic_only"):
        raise ValueError("Synthetic classifier metadata/feature order is invalid")
    models = {name: joblib.load(artifact_dir / filename) for name, filename in ARTIFACT_FILENAMES.items()}
    return {"metadata": metadata, "models": models}


def classify_synthetic_scenario(bundle: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    """Predict a generated-scenario resemblance, never a real-world fraud label."""
    metadata = bundle["metadata"]
    model_name = metadata["selected_model"]
    row = {name: features[name] for name in FEATURE_NAMES}
    frame = pd.DataFrame([row], columns=list(FEATURE_NAMES))
    probability = float(bundle["models"][model_name].predict_proba(frame)[0, 1])
    threshold = float(metadata["selected_threshold"])
    label = int(probability >= threshold)
    scenario = LABELS[label]
    return {
        "status": "SYNTHETIC_SCENARIO_EXPERIMENT",
        "model": model_name,
        "artifact_version": metadata["artifact_version"],
        "predicted_scenario": scenario,
        "synthetic_scenario_score": probability,
        "decision_threshold": threshold,
        "interpretation": f"This listing resembles the {scenario.replace('_', ' ').lower()} in generated training scenarios only.",
        "disclaimer": "Synthetic-scenario classifier output only. It is not a real-world fraud prediction, verified label, confidence score, or proof of seller intent.",
        "evaluation_scope": "SYNTHETIC_HELD_OUT_TEST_ONLY",
    }
