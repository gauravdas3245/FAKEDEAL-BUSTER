# FakeDeal Buster — Day 2, 5 PM ML Progress Demo

**Status:** Bounded real project-data train/validation smoke demo ready; full evaluation pending.  
**Dataset root:** `C:\end sem project\archive (5)`  
**Real-data demo command:** `C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe scripts/demo_real_data_smoke.py --data-dir "C:\end sem project\archive (5)"`  
**Test command:** `C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe -m pytest -q --basetemp="C:\end sem project\FAKEDEAL-BUSTER\.pytest-run" -p no:cacheprovider`

## Dataset location and split verification

The raw files were found at `C:\end sem project\archive (5)\data\splits`. They were read in place; no dataset files were copied or modified. DuckDB schema and census queries verified:

| Split | Rows | Columns | Date range | Products | Platforms |
|---|---:|---:|---|---:|---:|
| Train | 20,450,474 | 46 | 2023-01-01 to 2024-08-05 | 9,980 | 5 |
| Validation | 2,560,694 | 46 | 2024-08-06 to 2024-10-17 | 9,980 | 5 |
| Test | 2,595,772 | 46 | 2024-10-18 to 2024-12-30 | 9,980 | 5 |

The splits have identical column names and strictly non-overlapping chronological boundaries. The test split was read only for schema and boundary identification; it was not used for feature fitting, model fitting, or scoring. The earlier Day 1 exhaustive label census reported zero positive `fake_discount_flag` values. `price_spike_flag` is not used as fake-discount ground truth. Dataset documentation describes these observations as simulated retail prices, not verified real-world transactions.

## Bounded real-data train and validation smoke test

The reproducible script reads at most the first **100,000 training rows** through DuckDB, emits features in batches of at most 5,000, and fits preprocessing and Isolation Forest on a deterministic reservoir of **5,000** real project-file feature rows. It scores one observed training row solely to verify the end-to-end wiring. This observation is in the training sample; its output is not an evaluation result.

Observed training record: `P0000001`, Amazon, `2023-01-15`; current price **232.21**, original price **234.67**. The 30-day historical mean was approximately **214.06**, the 30-day sample standard deviation approximately **10.63**, and the 7-day maximum approximately **233.97**.

| Feature | Calculation | Real project-file smoke value |
|---|---|---:|
| `msrp_to_30d_avg` | 234.67 / historical 30-day mean | 1.09626 |
| `ratio_to_30d_avg` | 232.21 / historical 30-day mean | 1.08477 |
| `price_volatility_30d` | historical 30-day sample std / historical 30-day mean | 0.04967 |
| `recent_7d_surge` | max(0, (historical 7-day max − historical 30-day mean) / historical 30-day mean) | 0.09297 |

The fitted RobustScaler output was `[-0.88389, 0.48624, -0.71686, 0.25280]` in canonical feature order. The fitted Isolation Forest returned anomaly score **−0.15444**, `is_anomaly=false` for this training observation. The score is an unsupervised statistical indicator, not a fraud probability.

For a bounded validation smoke, the script uses the first ten product IDs seen in the training prefix, calculates their validation features with full earlier training history, and emits only validation-period rows. It scored **2,774** validation observations: **23** flagged anomalies (**0.8291%**). The score range was **−0.24896 to 0.03334**; mean **−0.17801**; quartiles **−0.21182 / −0.19099 / −0.15779**. This is a product-filtered smoke subset, not a full validation evaluation or a fraud-performance metric. The test split was not used.

The script defaults to a 100,000 raw-row cap, 5,000-row reservoir, 5,000-row output batches, and 50 trees. It sets DuckDB working memory to 1 GB. To change the bounded workload, use `--source-row-limit`, `--max-training-rows`, `--batch-size`, and `--n-estimators`. The separate `scripts/demo_synthetic_ml.py` remains available as a deterministic synthetic example.

## Pipeline and verification

The four model features are calculated from strictly prior observations in 30-day and 7-day **calendar** windows, partitioned by `(product_id, platform)`. Current and future observations are excluded; missing dates are not filled. Rows require at least 14 valid observations in the trailing 30 days. Validation feature calculation carries training history across the split boundary but emits only validation-period rows. Preprocessing is fit only on the training reservoir. Feature labels and forward targets are not model inputs; `discount_inflation_gap` remains an auxiliary value outside the Isolation Forest vector.

Latest full test run in the verified Conda environment: **40 passed**. Coverage includes hand-calculated formulas, missing dates, duplicate and invalid values, product/platform isolation, strict history, cross-split history, chronological boundary rejection, bounded batch/input rows, train-only scaling, deterministic fit, and model/preprocessor serialization.

## Teacher-demo talking points

- The audited dataset has chronological splits and 25.6 million simulated price observations.
- The fake-discount label has no positive examples, so a supervised fake-discount classifier cannot be trained from it.
- Four historical features measure the advertised reference price, current price, volatility, and recent surge against prior observed prices.
- Isolation Forest finds unusual feature combinations; it does not establish fraud.
- The real-data result is a capped training-split wiring demo only. No validation metrics or fraud-performance claims are available.

## Remaining work

1. Expand from the ten-product smoke subset to a documented, representative training reservoir and a broader validation score report; report this as anomaly analysis, not fraud classification.
2. Keep the later test split untouched until a deliberate final evaluation plan is approved.
3. Establish meaningful anomaly review and thresholds with domain/mentor input; do not invent FDI weights or claim calibrated probabilities.
4. Integrate ML inference with the backend and align the API contract with the backend/frontend owners.
5. Resolve conflicting license statements in the dataset documentation before redistribution.
