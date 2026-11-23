# Frozen Isolation Forest v1: untouched test-split evaluation

**Evaluation time (UTC):** 2026-11-17T14:37:42.726571+00:00  
**Evaluation:** anomaly detection only; model, scaler, and threshold unchanged.  
**Artifact:** `isolation_forest_v1`; source dataset is simulated e-commerce price observations; not verified real-world transactions.  
**Test labels:** not used. The test split was not used for fitting or threshold tuning.

## Data and score totals

- Test rows scanned/emitted: 2,595,772.
- Eligible/scored: 2,595,772; invalid engineered features: 0.
- Anomalies: 39,864 (1.5357%).
- Test timestamp range: 2024-10-18 00:00:00 to 2024-12-30 00:00:00.
- Runtime: 170.65 seconds; DuckDB cap 1GB; batch size 25,000.
- Historical context: train + validation + test rows are window input; only test-period rows are emitted. Strict prior calendar windows exclude the current/future timestamps.

### Anomaly-score distribution

| Statistic | Value |
|---|---:|
| Minimum (exact) | -0.253060635 |
| Maximum (exact) | 0.122761394 |
| Mean (exact) | -0.155493851 |
| 5th percentile (bounded deterministic reservoir) | -0.233194790 |
| 25th percentile (sample) | -0.204984274 |
| Median (sample) | -0.167128766 |
| 75th percentile (sample) | -0.117944344 |
| 95th percentile (sample) | -0.039259327 |

Quantiles use deterministic Algorithm R reservoirs per grouping; exact min, max, and mean are streaming aggregates.

## Anomaly rate by platform

| Platform | Scored | Anomalies | Rate | Mean score | Median score (sample) |
|---|---:|---:|---:|---:|---:|
| amazon | 513,264 | 9,009 | 1.7552% | -0.147867332 | -0.155479580 |
| bestbuy | 519,258 | 9,184 | 1.7687% | -0.144065328 | -0.148716708 |
| ebay | 521,404 | 6,909 | 1.3251% | -0.163548396 | -0.178714589 |
| flipkart | 519,628 | 6,853 | 1.3188% | -0.167830809 | -0.184843956 |
| walmart | 522,218 | 7,909 | 1.5145% | -0.154035589 | -0.165185865 |

## Anomaly rate by category

| Category | Scored | Anomalies | Rate | Mean score | Median score (sample) |
|---|---:|---:|---:|---:|---:|
| Appliances | 311,392 | 471 | 0.1513% | -0.171125596 | -0.180561881 |
| Books | 259,148 | 100 | 0.0386% | -0.175500704 | -0.185193610 |
| Electronics | 649,202 | 4,841 | 0.7457% | -0.159733117 | -0.169632372 |
| Fashion | 523,550 | 27,390 | 5.2316% | -0.124506753 | -0.134299990 |
| Gaming | 390,202 | 4,533 | 1.1617% | -0.155551562 | -0.166617579 |
| Household | 256,188 | 1,222 | 0.4770% | -0.165203829 | -0.175168287 |
| Sports | 206,090 | 1,307 | 0.6342% | -0.159903192 | -0.169576500 |

## Comparison with chronological validation

Validation anomaly rate: 1.1857%; test anomaly rate: 1.5357%; change: +0.3500 percentage points.
Mean anomaly score changed from -0.191805121 on validation to -0.155493851 on test (delta +0.036311270).
These comparisons describe distribution shift; they do not tune the threshold or measure classification accuracy.

| Platform | Validation rate | Test rate | Change (percentage points) |
|---|---:|---:|---:|
| amazon | 1.1787% | 1.7552% | +0.5766 |
| bestbuy | 1.1987% | 1.7687% | +0.5700 |
| ebay | 1.1025% | 1.3251% | +0.2225 |
| flipkart | 1.1765% | 1.3188% | +0.1423 |
| walmart | 1.2720% | 1.5145% | +0.2425 |

| Category | Validation rate | Test rate | Change (percentage points) |
|---|---:|---:|---:|
| Appliances | 0.0482% | 0.1513% | +0.1031 |
| Books | 0.0016% | 0.0386% | +0.0370 |
| Electronics | 0.3772% | 0.7457% | +0.3684 |
| Fashion | 4.5958% | 5.2316% | +0.6358 |
| Gaming | 0.7472% | 1.1617% | +0.4146 |
| Household | 0.2164% | 0.4770% | +0.2606 |
| Sports | 0.3128% | 0.6342% | +0.3214 |

## Prediction consistency

- Wrapper/direct score mismatches: 0.
- Wrapper/estimator flag mismatches: 0.
- Wrapper/raw prediction mismatches: 0.
- Flag/positive-wrapper-score mismatches: 0.
- The wrapper score is the negative decision function, so higher scores mean more anomalous.

## Classification metrics and limitations

**Classification accuracy, precision, recall, and F1 are not measurable from verified ground truth.** The candidate fake-discount label has zero positive examples and undocumented generation logic. The price-spike label is a different dataset anomaly signal, not fake-discount ground truth; it was excluded from scoring and metric calculation.

Anomaly detection rate is the fraction of test observations the frozen Isolation Forest flags as anomalous. It is not classification accuracy, fraud prevalence, or a probability that an item is fraudulent. The source dataset is synthetic, so these results do not establish real-world fraud-detection performance.

Artifact checksums matched before and after evaluation: **True**. Full machine-readable results: `C:\end sem project\FAKEDEAL-BUSTER\artifacts\ml\evaluations\v1_test_evaluation.json`.
