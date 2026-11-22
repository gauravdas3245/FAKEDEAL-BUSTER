# Dataset Validation Report: E-Commerce Product Price Tracker

**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Stage:** Stage 1 — Data Ingestion & Dataset Inspection  
**Date of Validation:** 2026-11-17  
**Auditor:** Antigravity / Gaurav Das  
**Environment:** `fakedeal` dedicated Conda environment (Python 3.12.16, DuckDB 2.0.0)

---

## 1. Executive Summary

This validation report documents the exhaustive inspection of the approved primary dataset for the FakeDeal Buster machine learning pipeline. Inspection was executed using memory-bounded DuckDB queries without loading raw CSV files into Pandas memory.

### Key Milestones & Critical Findings:
1. **Exhaustive Row Count Verified:** Exactly **25,606,940 rows** across three chronological splits, matching dataset source specifications with 100% fidelity. Total disk size is **7.70 GB (8,266,973,494 bytes)**.
2. **Strict Chronological Separation:** The three splits (`train`, `val`, `test`) have strictly non-overlapping, sequential time boundaries spanning January 1, 2023 through December 30, 2024.
3. **`fake_discount_flag` Zero-Variance Discovery:** An exhaustive census of all 25,606,940 records revealed exactly **0 positive labels** (`fake_discount_flag == 1` count is 0). Supervised binary classification on this label is mathematically and practically impossible.
4. **Resolution of `ecommerce_anomalies.csv` Identity:** The file `ecommerce_anomalies.csv` contains exactly 48,554 records. This exactly matches the sum of all `price_spike_flag == 1` records across the three temporal splits ($28,542 + 806 + 19,206 = 48,554$). It is an extracted anomaly subset, not a representative dataset.
5. **Architectural Direction:** The system must utilize an **unsupervised anomaly detection model (Isolation Forest)** paired with a deterministic, domain-grounded **Fake Discount Index (FDI)** heuristic scoring engine, rather than a supervised classifier.

---

## 2. Dataset Metadata & Provenance

- **Dataset Name:** E-Commerce Product Price Tracker Dataset
- **Author:** Amith Nair
- **Source:** Kaggle (`https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset`)
- **Verified License:** **CC0 1.0 Universal (Public Domain Dedication)**  
  *(Verified directly from `LICENSE.txt` and `README.md` in the dataset distribution archive)*
- **Primary Physical Files:**
  - `data/splits/ecommerce_train.csv`
  - `data/splits/ecommerce_val.csv`
  - `data/splits/ecommerce_test.csv`
- **Total Columns:** 46
- **Tracking Universe:** 9,980 unique product IDs continuously tracked across 5 platforms (`amazon`, `flipkart`, `ebay`, `walmart`, `bestbuy`).

---

## 3. Exhaustive Census Results by Temporal Split

All statistics in this section were computed via full-table scans using DuckDB's streaming aggregation engine. None of these metrics rely on sample extrapolations.

| Metric | Train Split (`ecommerce_train.csv`) | Validation Split (`ecommerce_val.csv`) | Test Split (`ecommerce_test.csv`) | Full Dataset Total |
|---|---|---|---|---|
| **Inspection Status** | Exhaustive Census Complete | Exhaustive Census Complete | Exhaustive Census Complete | **25,606,940 Rows Audited** |
| **File Size on Disk** | 6.16 GB (6,609,097,454 bytes) | 787.64 MB (825,896,977 bytes) | 793.44 MB (831,979,063 bytes) | **7.70 GB (8,266,973,494 bytes)** |
| **Row Count** | 20,450,474 | 2,560,694 | 2,595,772 | **25,606,940** |
| **Split Percentage** | 79.86% | 10.00% | 10.14% | 100.00% |
| **Earliest Timestamp** | 2023-01-01 00:00:00 | 2024-08-06 00:00:00 | 2024-10-18 00:00:00 | **2023-01-01 00:00:00** |
| **Latest Timestamp** | 2024-08-05 00:00:00 | 2024-10-17 00:00:00 | 2024-12-30 00:00:00 | **2024-12-30 00:00:00** |
| **Temporal Overlap** | None (Precedes Val) | None (Between Train & Test) | None (Follows Val) | **Strictly Sequential** |
| **`fake_discount_flag == 1`** | **0 (0.0000%)** | **0 (0.0000%)** | **0 (0.0000%)** | **0 (0.0000%)** |
| **`fake_discount_flag == 0`** | 20,450,474 (100.0000%) | 2,560,694 (100.0000%) | 2,595,772 (100.0000%) | 25,606,940 (100.0000%) |
| **`fake_discount_flag` Nulls**| 0 | 0 | 0 | 0 |
| **`price_spike_flag == 1`** | 28,542 (0.1396%) | 806 (0.0315%) | 19,206 (0.7399%) | **48,554 (0.1896%)** |
| **`price_spike_flag == 0`** | 20,421,932 (99.8604%) | 2,559,888 (99.9685%) | 2,576,566 (99.2601%) | 25,558,386 (99.8104%) |
| **`price_spike_flag` Nulls** | 0 | 0 | 0 | 0 |
| **Unique Products** | 9,980 | 9,980 | 9,980 | 9,980 |
| **Unique Platforms** | 5 | 5 | 5 | 5 |
| **Scan Execution Time** | 10.80 seconds | 1.93 seconds | 1.94 seconds | **14.67 seconds** |

---

## 4. Missing-Value Census

Missing values were tallied column-by-column across all 46 columns in each split:

### Train Split:
- **Columns with missing values:**
  - `price_change_abs`: 35,078 nulls (0.1715%)
  - `price_change_pct`: 35,078 nulls (0.1715%)
  - `price_7d_std`: 35,078 nulls (0.1715%)
  - `price_30d_std`: 35,078 nulls (0.1715%)
  - `price_volatility_30d`: 35,078 nulls (0.1715%)
- **Root Cause:** Rolling historical statistics require prior observations. At the start of the temporal series (January 2023), initial window lookbacks produce expected boundary nulls.
- **Other 41 columns:** Exactly 0 nulls (100% complete).

### Validation Split:
- **All 46 columns:** Exactly 0 nulls (100% complete). Rolling features have full lookback history from the preceding train window.

### Test Split:
- **Columns with missing values:**
  - `target_price_7d`: 245,546 nulls (9.4595%)
  - `target_price_30d`: 1,052,340 nulls (40.5405%)
- **Root Cause:** Forward-looking future target prices cannot be calculated for records occurring within 7 or 30 days of the dataset's terminal date (December 30, 2024).
- **Other 44 columns:** Exactly 0 nulls (100% complete).

---

## 5. Domain & Integrity Checks (Sample-Level & Aggregate-Level)

### Aggregate Integrity Checks:
- **Minimum Price:** 1.00 (Valid, no negative or zero prices).
- **Maximum Price:** 5,112.69 (Consistent with consumer electronics, computers, and appliances).
- **Minimum Original Price:** 2.63.
- **Maximum Original Price:** 5,326.01.
- **Discount Percentage Range:** 0.1% to 83.8% (All within legitimate commercial bounds; no negative discounts).

### Sample-Level Sequential Preview (First 3 Rows of Each Split):

#### Train Preview (`LIMIT 3 OFFSET 0`):
| product_id | title | platform | timestamp | price | original_price | discount_pct |
|---|---|---|---|---|---|---|
| P0000001 | Google Max Smartphones (Green) | amazon | 2023-01-01 | 203.92 | 221.26 | 7.8% |
| P0000001 | Google Max Smartphones (Green) | amazon | 2023-01-02 | 203.08 | 225.74 | 10.0% |
| P0000001 | Google Max Smartphones (Green) | amazon | 2023-01-03 | 210.15 | 221.45 | 5.1% |

#### Validation Preview (`LIMIT 3 OFFSET 0`):
| product_id | title | platform | timestamp | price | original_price | discount_pct |
|---|---|---|---|---|---|---|
| P0000001 | Google Max Smartphones (Green) | amazon | 2024-08-06 | 163.12 | 238.52 | 31.6% |
| P0000001 | Google Max Smartphones (Green) | amazon | 2024-08-07 | 163.18 | 226.25 | 27.9% |
| P0000001 | Google Max Smartphones (Green) | amazon | 2024-08-08 | 161.93 | 240.78 | 32.7% |

#### Test Preview (`LIMIT 3 OFFSET 0`):
| product_id | title | platform | timestamp | price | original_price | discount_pct |
|---|---|---|---|---|---|---|
| P0000001 | Google Max Smartphones (Green) | amazon | 2024-10-18 | 204.21 | 229.86 | 11.2% |
| P0000001 | Google Max Smartphones (Green) | amazon | 2024-10-19 | 202.07 | 233.67 | 13.5% |
| P0000001 | Google Max Smartphones (Green) | amazon | 2024-10-20 | 192.23 | 227.69 | 15.6% |

---

## 6. Architectural Consequences & Machine Learning Strategy

1. **Rejection of Supervised Classifier for Fake Discounts:**
   Because `fake_discount_flag` has zero positive instances across 25.6M records, training a supervised classification model (such as Logistic Regression, Random Forest, or XGBoost) to predict fake discounts directly from this label would fail catastrophically (predicting 0 for all instances).

2. **Unsupervised Outlier Detection + Domain FDI Rule Engine:**
   - **Isolation Forest:** Train an Isolation Forest on feature vectors capturing historical price stability, relative price deviation from 30-day and 60-day rolling medians, and discount magnitude. This identifies statistical pricing anomalies without relying on artificial ground truth flags.
   - **Fake Discount Index (FDI):** Construct a transparent, deterministic composite heuristic score ($0 - 100$) evaluating:
     - Pre-sale artificial markup (MSRP inflation shortly before sale events).
     - Discount claim versus true historical median price.
     - Frequency of discounted pricing (perpetual sale detection).
   - **Verdict Categorization:**
     - `Potential Fake Discount` (FDI $\ge 70$, high pre-sale price inflation)
     - `Suspicious Pricing` (FDI $45 - 69$, statistical anomaly detected)
     - `No Strong Fake-Discount Signal` (FDI $< 45$, genuine price drop)
     - `Needs More Data` (Insufficient history, $< 14$ days of observations)

3. **Strict Memory Management Pipeline:**
   - All dataset loading, feature computation, and model batch ingestion will utilize streaming queries via `DuckDB` or bounded chunking via `stream_batches()`.
   - Never load the 6.16 GB training split directly into memory.

---

## 7. Stage 1 Sign-Off Status

- **Status:** **STAGE 1 COMPLETE & EMPIRICALLY VERIFIED**
- **Artifacts Implemented:**
  - `ml/data_loader.py` (Memory-safe DuckDB streaming, bounds checking, path escaping, schema inspector)
  - `ml/inspect_dataset.py` (Full census auditor with performance timing)
  - `tests/test_data_loader.py` (19 automated unit tests, 100% pass rate)
  - `dataset/validation-report.md` (Updated with complete empirical findings)
- **Ready for Next Stage:** Awaiting user sign-off to proceed to Stage 2 (Feature Engineering & Baseline Scoring Engine).
