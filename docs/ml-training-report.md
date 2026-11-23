# Isolation Forest Training Report

**Training timestamp (UTC):** 2026-11-17T11:45:23.687037+00:00  
**Dataset:** synthetic E-Commerce Product Price Tracker; no verified fraud labels.  
**Random seed:** 20261117  
**Feature order:** `msrp_to_30d_avg, ratio_to_30d_avg, price_volatility_30d, recent_7d_surge`

## Training population

- Full source rows scanned: **20,450,474**.
- Eligible feature rows: **19,959,382**.
- Excluded feature rows: **491,092**.
- Reservoir rows used: **100,000** (uniform Algorithm R reservoir across the complete eligible stream).
- Training range: 2023-01-01 00:00:00 to 2024-08-05 00:00:00.
- Training/runtime: 300.42 seconds.
- Exclusions: `{"insufficient_prior_history_or_invalid_derived_baseline": 491092, "missing_price_or_original_price": 0, "missing_product_platform_or_timestamp": 0, "non_finite_price_or_original_price": 0, "non_positive_price_or_original_price": 0}`.
- Scaler fit and Isolation Forest fit used training rows only.

## Chronological validation

- Full validation source rows: **2,560,694**.
- Eligible/scored rows: **2,560,694**.
- Excluded feature rows: **0**.
- Validation range: 2024-08-06 00:00:00 to 2024-10-17 00:00:00.
- Anomalies: **30,363 / 2,560,694** (1.1857%).
- Validation scoring runtime: 874.87 seconds.
- Non-finite engineered feature rows: 0.
- Exclusions: `{"insufficient_prior_history_or_invalid_derived_baseline": 0, "missing_price_or_original_price": 0, "missing_product_platform_or_timestamp": 0, "non_finite_engineered_features": 0, "non_finite_price_or_original_price": 0, "non_positive_price_or_original_price": 0}`.

### Validation anomaly-score distribution

| Statistic | Value |
|---|---:|
| Minimum | -0.25368759 |
| Maximum | 0.11310916 |
| Mean | -0.19180512 |
| 5th percentile (sample) | -0.23885760 |
| 25th percentile (sample) | -0.22530194 |
| Median (sample) | -0.20798975 |
| 75th percentile (sample) | -0.17682321 |
| 95th percentile (sample) | -0.08420011 |

Quantiles use a deterministic reservoir of 100,000 validation scores; min, max, and mean are exact.

### By platform

| Platform | Scored | Anomalies | Rate | Mean score | Median score (sample) |
|---|---:|---:|---:|---:|---:|
| amazon | 506,328 | 5,968 | 1.1787% | -0.19016882 | -0.20570182 |
| bestbuy | 512,241 | 6,140 | 1.1987% | -0.18826953 | -0.20371752 |
| ebay | 514,358 | 5,671 | 1.1025% | -0.19462330 | -0.21056496 |
| flipkart | 512,606 | 6,031 | 1.1765% | -0.19443361 | -0.21124472 |
| walmart | 515,161 | 6,553 | 1.2720% | -0.19149967 | -0.20768496 |

### By product category

| Category | Scored | Anomalies | Rate | Mean score | Median score (sample) |
|---|---:|---:|---:|---:|---:|
| Appliances | 307,184 | 148 | 0.0482% | -0.20687416 | -0.21468949 |
| Books | 255,646 | 4 | 0.0016% | -0.20717611 | -0.21168494 |
| Electronics | 640,429 | 2,416 | 0.3772% | -0.19842039 | -0.21223219 |
| Fashion | 516,475 | 23,736 | 4.5958% | -0.15787439 | -0.17826362 |
| Gaming | 384,929 | 2,876 | 0.7472% | -0.19349369 | -0.20911199 |
| Household | 252,726 | 547 | 0.2164% | -0.20242018 | -0.21382514 |
| Sports | 203,305 | 636 | 0.3128% | -0.19867454 | -0.21253249 |

## Interpretation and limits

The model is an unsupervised statistical anomaly detector. Anomaly labels and scores describe unusual feature combinations under this fitted Isolation Forest; they are not calibrated probabilities and do not establish fake discounts or fraud.
The dataset is simulated and `fake_discount_flag` has zero positive examples. No accuracy, precision, recall, F1, or fraud-detection performance is reported. The test split was not opened for training, threshold tuning, or validation.

## Memory and reproducibility

DuckDB memory cap: 1GB; output batch size: 50,000; reservoir matrix: approximately 3,200,000 bytes. Intermittent Windows process working-set checks during the run reached 1,237,281,216 bytes (about 1.15 GiB). This is the largest sampled working set observed, not a guaranteed process peak; `psutil` was unavailable for continuous peak-RSS measurement.

## Artifacts

Versioned directory: `C:\end sem project\FAKEDEAL-BUSTER\artifacts\ml\isolation_forest_v1`. See `checksums.sha256` for file integrity hashes.
