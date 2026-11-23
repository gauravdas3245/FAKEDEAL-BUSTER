# Synthetic discount scenario experiment

## Scope and label governance

This separate experiment exists because the teacher approved synthetic data generation. Its labels are **generator scenario labels**, not verified real-world discount fraud. The original dataset is unchanged. Existing `fake_discount_flag` and `price_spike_flag` are not used as targets.

The generator samples 60,000 valid feature profiles reproducibly from the original chronological training split using DuckDB reservoir sampling. It selects only actual platform/category and historical price feature columns; it does not select product IDs, fraud labels, spike labels, or future target columns. See `artifacts/synthetic/discount_scenarios_v1/manifest.json` for the actual sampled min/p05/median/p95/max ranges, seed, split counts, and SHA-256 values.

Each generated case receives a distinct sampled source profile. Labels are assigned as a balanced latent generator condition, then scenario prices/features are generated from source-derived price ratios, discounts, volatility, and surge ranges:

- `0 SYNTHETIC_GENUINE_DISCOUNT`: current-to-30-day-average ratio is sampled from observed below-average ratios; advertised discount magnitude is sampled from observed discount magnitudes.
- `1 SYNTHETIC_ARTIFICIALLY_INFLATED_DISCOUNT`: current price stays near an observed historical baseline while the advertised reference price is inflated using a documented seeded factor based on sampled original-price-to-average ranges.

The target column is `scenario_label`; `scenario_name` is display metadata. Neither appears in the model feature list. This is a supervised experiment on constructed scenarios and can measure only recovery of those generator rules.

## Data split and preprocessing

Seed: `20261118`. There are 40,000 generated examples in separate CSVs: 28,000 train, 6,000 validation, and 6,000 test; each split has equal scenario classes. These are independent IID offers, not a time series, so a stratified random split is used. The data manifest and model metadata record split checksums and seed.

Features (fixed order):

1. `msrp_to_30d_avg`
2. `ratio_to_30d_avg`
3. `price_volatility_30d`
4. `recent_7d_surge`
5. `advertised_discount_pct`
6. `platform`
7. `category`

The first four values use the existing dataset definitions and are obtained in production directly from the central Isolation Forest result. The advertised discount is recomputed from submitted prices. Category/platform are actual resolved catalogue metadata. No seller features or new time-series feature calculations are introduced.

Both model pipelines impute numeric missing values, one-hot encode platform/category, and fit all preprocessing only on the training split. Logistic Regression additionally standard-scales numeric inputs. Logistic Regression uses class weighting; Random Forest uses balanced-sub-sample class weights, bounded depth, minimum leaf size, and fixed seeds.

## Threshold and synthetic test metrics

Thresholds are selected using validation only: maximize recall for the artificial scenario subject to at most 10% false-positive rate on synthetic genuine scenarios. Model selection uses validation recall, then PR-AUC and precision. The test split is not used for threshold/model selection. Test classes each have support 3,000. The reported Gini coefficient is `2*ROC-AUC-1`; Random Forest Gini impurity is not the same metric.

| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC (average precision) | Gini | Confusion matrix TN/FP/FN/TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.6800 | 0.8799 | 0.6670 | 0.7588 | 0.8891 | 0.9019 | 0.7782 | 2727 / 273 / 999 / 2001 |
| Random Forest | 0.4100 | 0.8954 | 0.7360 | 0.8079 | 0.9160 | 0.9308 | 0.8320 | 2742 / 258 / 792 / 2208 |

Random Forest was selected using validation-only criteria. These are **synthetic held-out test metrics only**, not real-world fraud accuracy, seller risk, or marketplace performance. Dataset and artifact details are in `artifacts/synthetic/discount_scenarios_v1/` and `artifacts/ml/synthetic_discount_v1/`.

## Application integration

`POST /api/analyze` and `POST /api/inspect` include a separate `synthetic_classifier` field. It reports resemblance to one of the generated scenarios and uses no top-level verdict, FDI component, or Isolation Forest score as a substitute. Its score is not a calibrated real-world fraud probability or confidence. The React result card displays the scenario label and disclaimer. `GET /api/models/synthetic-comparison` exposes only clearly labelled synthetic test metrics.

If this classifier bundle is absent or checksum validation fails, the field reports unavailable and the existing central anomaly analysis continues. Insufficient central history prevents synthetic classifier inference because its four historical inputs are unavailable. The production `isolation_forest_v1` bundle, FDI implementation, and conditional forecast remain separate and unchanged.

## Reproduce

From repository root, in the existing `fakedeal` environment:

```cmd
"C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\generate_synthetic_discount_dataset.py --rows 40000 --sample-size 60000 --seed 20261118 --overwrite
"C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\train_synthetic_discount_classifiers.py --rf-estimators 200 --seed 20261118 --overwrite
```

Generation refuses to overwrite non-empty outputs unless `--overwrite` is explicitly supplied. No package installation is required.
