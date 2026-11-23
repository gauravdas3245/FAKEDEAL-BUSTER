# Machine Learning

## Finalized feature pipeline

- `feature_extractor.py` calculates the canonical four-feature vector with strictly prior 30/7 calendar windows grouped by `(product_id, platform)`. It does not fill missing dates and requires 14 prior observations in the 30-day window.
- `preprocessor.py` aligns the canonical feature order and supports train-fitted RobustScaler or StandardScaler persistence.
- `isolation_forest.py` wraps scikit-learn Isolation Forest. Its anomaly score is not a calibrated probability or proof of fraud.
- `train_pipeline.py` uses DuckDB with bounded output batches, a 1 GB default query memory cap, deterministic Algorithm R reservoir sampling, training-only preprocessing/model fitting, and validation scoring with training history carried across the split boundary.

`discount_inflation_gap` is auxiliary and remains outside the Isolation Forest feature vector. No target or label columns are model inputs.

## Final trained artifact

The completed version is in `artifacts/ml/isolation_forest_v1/`. It contains the fitted Isolation Forest, fitted scaler, metadata, full validation summary, a fixed prediction fixture, and SHA-256 checksums. The accompanying report is `docs/ml-training-report.md`.

Verified run configuration:

- Full training source: 20,450,474 rows; 19,959,382 eligible features.
- Reservoir: 100,000 rows, seed `20261117`.
- Isolation Forest: 200 estimators, contamination `0.01`, `max_samples="auto"`.
- Validation: full 2,560,694-row validation split; test split not used.

## Reproduce

Run from the repository root with the configured Conda environment. Training is a full-split operation and may take several minutes. Use a new version directory when retraining; the script refuses a non-empty artifact directory.

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\train_final_model.py `
  --data-root "C:\end sem project\archive (5)" `
  --artifact-dir artifacts\ml\isolation_forest_v2 `
  --reservoir-size 100000 --seed 20261117 --n-estimators 200 `
  --contamination 0.01 --batch-size 50000 --duckdb-memory-limit 1GB
```

The command scans all training rows using DuckDB, fits only on the training reservoir, scores the complete validation split in batches, writes metadata and checksums, and launches the artifact validator in a fresh Python process.

Verify the saved version independently:

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\validate_final_model.py `
  --artifact-dir artifacts\ml\isolation_forest_v1
```

Inspect the saved metadata and load the model/preprocessor directly:

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" -c "import json; from pathlib import Path; from ml.isolation_forest import IsolationForestDetector; from ml.preprocessor import FeaturePreprocessor; p=Path('artifacts/ml/isolation_forest_v1'); print(json.loads((p/'metadata.json').read_text())['model']); model=IsolationForestDetector.load(p/'isolation_forest.joblib'); scaler=FeaturePreprocessor.load_json(p/'preprocessor.json'); print(model.is_fitted, scaler.feature_names)"
Get-Content artifacts\ml\isolation_forest_v1\metadata.json
```

For inference, construct the four raw feature values in the exact order recorded in metadata, pass them through `scaler.transform_single(feature_dict)`, then call `model.predict_anomaly(scaled_vector)`.

Run all tests:

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" -m pytest -q `
  --basetemp="C:\end sem project\FAKEDEAL-BUSTER\.pytest-run" -p no:cacheprovider
```

## Interpretation limits

The source dataset is simulated and `fake_discount_flag` has zero positive examples. Validation anomaly rates describe this fitted unsupervised detector only. They do not establish fake discounts, fraud, or real-world detection performance. Do not report classifier accuracy, precision, recall, or F1 from these labels.

## Separate synthetic supervised experiment

`synthetic_discount.py` and `synthetic_classifier.py` implement a separate generated-scenario experiment. It samples feature ranges from the original training split, creates explicit generator-only labels, and trains LR/RF pipelines with train-only preprocessing and held-out synthetic evaluation. It does not use original target flags or modify `isolation_forest_v1`. Its outputs are scenario resemblance only, never real-world fraud probabilities. Reproduce and review metrics using [`docs/synthetic-discount-experiment.md`](../docs/synthetic-discount-experiment.md).

## Reusable inference

`inference.py` verifies the v1 checksum manifest, metadata and feature order, then loads the saved detector and train-fitted preprocessor once into an `InferenceEngine`. Reuse that instance across requests. It applies the same formulas and calendar `RANGE` window convention as the training SQL and returns structured `OK` / `NEEDS_MORE_DATA` results; invalid single observations raise `InferenceValidationError`. Batch mode returns independent `INVALID_INPUT` results for bad items without stopping neighboring predictions.

The model wrapper defines `anomaly_score` as the negative of scikit-learn's `decision_function`; higher means more anomalous. The anomaly flag is the estimator's own `predict()` result (`-1`). Neither score nor flag is a fraud probability or proof. Feature explanations are descriptive, not causal attributions. Details and the backend-neutral integration contract are in [`docs/ml-inference-guide.md`](../docs/ml-inference-guide.md).

Demo the saved v1 model with labelled synthetic examples:

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\demo_inference.py
```

Initialize with `load_inference_engine("artifacts/ml/isolation_forest_v1")`, then reuse `engine.predict_product_observation(...)`, `engine.predict_batch(...)`, or streaming `engine.iter_predict_batch(...)`. The historical store must supply records for exactly one `(product_id, platform)` key. Inference uses the training SQL calendar ranges `[timestamp - 30 days, timestamp)` and `[timestamp - 7 days, timestamp)`, requires at least 14 distinct valid dates in 30 days and one observation in 7 days, and returns `NEEDS_MORE_DATA` if insufficient. Invalid/missing price values are rejected, and missing dates are not filled.

## Provisional Fake Discount Index

`fdi.py` keeps the proposed heuristic index separate from Isolation Forest features and returns `validation_status="PROVISIONAL_NOT_VALIDATED"`. The inference adapter recomputes `discount_pct` and `real_discount_30d` from the supplied prices and verified inference feature output; it can also expose `S_mean_ratio` and `S_msrp_inflation` when historical inference succeeds. The audit found no verified live calculation for dataset-only `price_spike_flag` and no definition for `pre_discount_hike_ratio`. The adapter therefore returns `INSUFFICIENT_INPUTS`, null official FDI/level, missing signals, and any computable component scores. It does not use either dataset flags or the Isolation Forest score as substitutes, omit weights, or renormalize.

The proposed scores, weights and bands remain hypotheses, not validated thresholds or fraud claims. See [`docs/fdi-methodology.md`](../docs/fdi-methodology.md) for the audit, formulas and backend-neutral contract. To run labelled synthetic illustrations:

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\demo_fdi.py
```

## Backend service entry point

For application integration, use `from ml.service import load_ml_service` and initialize once per process. Call `service.analyze_product_observation(...)`; it coordinates historical inference and FDI without duplicating feature math. The FastAPI backend initializes this service once and supplies actual strictly prior observations from the indexed derived store. Product resolution/data retrieval belong to the backend; feature calculations and prediction semantics remain in this central ML service. The compact handoff extract is not the production catalogue/history store. See [`docs/ml-backend-integration.md`](../docs/ml-backend-integration.md), [`backend/API_CONTRACT.md`](../backend/API_CONTRACT.md), and [`docs/dataset-processing.md`](../docs/dataset-processing.md).
