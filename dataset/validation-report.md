# FakeDeal Buster – Final Synchronized Dataset Validation Report

> **Document Status:** FINAL RECONCILED SPECIFICATION  
> **Prepared by:** Senior Data Engineer & Data Quality Analyst (Lakhyajyoti Phukan)  
> **Audited for:** Gaurav Das (ML Developer) & Faculty Mentor  
> **Effective Date:** 2026-11-17  
> **Replaces:** `dataset/validation-report.md` (which contained placeholder 'Pending' entries)

---

## 1. Executive Summary & Quality Scorecard

This report presents the complete empirical validation findings for the *E-Commerce Product Price Tracker Dataset* (Amith Nair, Kaggle).

All findings replace earlier placeholder "Pending" entries with **verified empirical metrics** derived from:
1. An **exhaustive 100% streaming census** across all 25,606,940 records.
2. A **deep-profile audit** of the full 2,560,694-row validation split (`ecommerce_val.csv`).
3. Empirical benchmarking on the **99,919-row prototype training sample**, the **20,000-row natural validation bench**, and the newly generated **20,000-row natural test sample**.

---

## 2. Dataset Dimensions & Split Architecture

| Metric | Verified Empirical Value | Evidence Source |
|---|---|---|
| **Total Rows (Census)** | **25,606,940** | Full streaming census across all raw splits (`ecommerce_train` + `val` + `test`). |
| **Total Raw Columns** | **46** | Verified against CSV headers and `metadata.json` (100% match). |
| **Total Prototype Columns** | **59** | 46 original + 13 added features/metadata in prototype evaluation samples. |
| **Date Range Covered** | **2023-01-01 to 2024-12-30** | Exactly 730 consecutive calendar days (2 full years). |
| **Unique Catalog Products** | **10,000** | Documented catalog-level items; 9,980 observed in 73-day validation window. |
| **E-Commerce Platforms (5)** | `amazon`, `bestbuy`, `ebay`, `flipkart`, `walmart` | Architectural target: ~20% uniform distribution. *(See Section 2.2 for exact counts).* |
| **Product Categories (7)** | `Electronics`, `Fashion`, `Gaming`, `Appliances`, `Books`, `Household`, `Sports` | Targets: 25%, 20%, 15%, 12%, 10%, 10%, 8%. *(Val split matches within 0.01%–0.17%).* |
| **Subcategories** | **35** | Exactly 5 distinct subcategories per main category. |

---

### 2.1 Chronological Split Verification & File Inventory

| Split / File Name | Physical File Path | Exact File Size (Bytes) | Decimal Size | Binary Size | Total Data Rows | Share (%) | Verified Date Window |
|---|---|---|---|---|---|---|---|
| **Full Processed** | `data/full/ecommerce_full.csv/ecommerce_processed.csv` | 8,266,972,621 B | 8.27 GB | 7.70 GiB | 25,606,940 | 100.00% | 2023-01-01 to 2024-12-30 (730 days) |
| **Training Split** | `data/splits/ecommerce_train.csv` | 6,609,097,454 B | 6.61 GB | 6.16 GiB | 20,450,474 | 79.86% | 2023-01-01 to 2024-08-05 (583 days) |
| **Validation Split** | `data/splits/ecommerce_val.csv` | 825,896,977 B | 0.83 GB | 0.77 GiB | 2,560,694 | 10.00% | 2024-08-06 to 2024-10-17 (73 days) |
| **Test Split** | `data/splits/ecommerce_test.csv` | 831,979,063 B | 0.83 GB | 0.77 GiB | 2,595,772 | 10.14% | 2024-10-18 to 2024-12-30 (74 days) |
| **Anomalies Subset** | `data/subsets/ecommerce_anomalies.csv` | 15,853,671 B | 15.85 MB | 15.12 MiB | 48,554 | 0.19% | 2023-01-01 to 2024-12-30 (`price_spike_flag == 1`) |
| **Forecast Subset** | `data/subsets/ecommerce_forecast.csv` | 8,190,424,833 B | 8.19 GB | 7.63 GiB | 25,356,940 | 99.02% | 2023-01-01 to 2024-12-23 (ends 7d early) |
| **Recommendation** | `data/subsets/ecommerce_recommendation.csv` | 5,780 B | 5.78 KB | 5.64 KiB | 100 | — | Catalog summary (14 columns) |
| **Total Extracted** | All CSV Files Combined | 24,740,230,399 B | 24.74 GB | 23.04 GiB | — | — | — |
| **Compressed Archive** | `archive (1).zip` | 4,475,346,654 B | 4.48 GB | 4.17 GiB | — | — | — |

---

### 2.2 Platform & Category Distribution by Scope

> [!WARNING]
> **Scope Distinction:** Never substitute validation-split distributions for full-dataset distributions. Full-dataset platform counts were not profiled in a separate census pass.

**Platform Breakdown across Evaluated Scopes:**
- **Validation Split (`ecommerce_val.csv`, $n=2,560,694$):**
  - Walmart: 515,161 rows (20.12%)
  - eBay: 514,358 rows (20.09%)
  - Flipkart: 512,606 rows (20.02%)
  - BestBuy: 512,241 rows (20.00%)
  - Amazon: 506,328 rows (19.77%)
- **Prototype Train Sample (`prototype_train_sample_100k.csv`, $n=99,919$ total):**
  - eBay: 20,246 rows (20.26%)
  - Walmart: 20,129 rows (20.15%)
  - BestBuy: 20,066 rows (20.08%)
  - Flipkart: 19,827 rows (19.84%)
  - Amazon: 19,651 rows (19.67%)
- **Natural Validation Bench (`natural_val_sample_20k.csv`, $n=20,000$):**
  - BestBuy: 4,082 rows (20.41%)
  - eBay: 4,037 rows (20.19%)
  - Walmart: 4,030 rows (20.15%)
  - Amazon: 3,927 rows (19.64%)
  - Flipkart: 3,924 rows (19.62%)
- **Natural Test Sample (`natural_test_sample_20k.csv`, $n=20,000$):**
  - Amazon: 4,047 rows (20.24%)
  - Walmart: 4,039 rows (20.19%)
  - eBay: 4,000 rows (20.00%)
  - Flipkart: 3,977 rows (19.89%)
  - BestBuy: 3,937 rows (19.69%)

**Category Breakdown in Validation Split (`ecommerce_val.csv`, $n=2,560,694$):**
- Electronics: 640,429 rows (25.01%) [Target: 25%]
- Fashion: 516,475 rows (20.17%) [Target: 20%]
- Gaming: 384,929 rows (15.03%) [Target: 15%]
- Appliances: 307,184 rows (12.00%) [Target: 12%]
- Books: 255,646 rows (9.98%) [Target: 10%]
- Household: 252,726 rows (9.87%) [Target: 10%]
- Sports: 203,305 rows (7.94%) [Target: 8%]

---

## 3. Comprehensive Data Quality & Boundary Checks

The full validation split (2,560,694 rows) was subjected to exhaustive data quality tests:

| Validation Rule | Inspected Rows | Violations Found | Error Rate | Status |
|---|---|---|---|---|
| **Missing Values (Core Fields)** | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Missing Values (Rolling Stats)** | 2,560,694 | 0 | 0.00% | **PASSED** (100% complete post-warmup) |
| **Duplicate Composite Keys** `(PID, Plat, TS)` | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Exact Duplicate Rows** | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Selling Price $\le 0$** | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Original Price (MSRP) $\le 0$** | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Negative Discount ($< 0\%$)** | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Discount Outside Bounds ($> 100\%$)** | 2,560,694 | 0 | 0.00% | **PASSED** (Max observed = 90.0%) |
| **Price $>$ Original Price** | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Malformed / Invalid Timestamps** | 2,560,694 | 0 | 0.00% | **PASSED** |
| **Timestamps Out of Order** | 2,560,694 | 0 | 0.00% | **PASSED** (Strict chronological order) |

> [!NOTE]
> **Rolling-Window Saturation Findings:**
> - In `ecommerce_train.csv` at $t=0$ (`2023-01-01`), exactly 86 observations contain empty values for 5 differential lag columns (`price_change_abs`, `price_change_pct`, `price_7d_std`, `price_30d_std`, `price_volatility_30d`) due to undefined prior-day variance. Discarding the Day 1–30 warm-up period completely eliminates these nulls.
> - **7-day and 30-day features** are fully saturated after the 30-day warm-up cutoff (`2023-01-31`).
> - **52-week features** (`price_52w_min`, `price_52w_max`) represent expanding inception-to-date extremes until Day 365 (`2023-12-31`). At Validation (Day 584) and Test (Day 657), they are 100% saturated.

---

## 4. Target Label & Anomaly Indicator Census

An exhaustive census across all 25,606,940 records yielded critical findings regarding dataset indicator flags:

| Target / Flag Column | Train Count (20.45M) | Val Count (2.56M) | Test Count (2.60M) | Total Census Count (25.6M) | Empirical Assessment |
|---|---|---|---|---|---|
| **`fake_discount_flag`** | **0** (0.00%) | **0** (0.00%) | **0** (0.00%) | **0 (0.0000%)** | **DEFUNCT AS TARGET:** Exactly 0 positive records across entire dataset. Cannot be used as a classification target. |
| **`price_spike_flag`** | **28,542** (0.1396%) | **806** (0.0315%) | **19,206** (0.7399%) | **48,554 (0.1896%)** | **ACTIVELY POPULATED:** Exactly matches row count of `ecommerce_anomalies.csv` (48,554 rows). Reflects statistical price volatility, NOT verified fraud. |

---

## 5. Prototype Dataset Validation & Proposed FDI Results

### 5.1 Dataset Composition & Disjointness Audit

| Dataset Artifact | Total Rows | Partition Breakdown | Spike Flag Count | Disjointness Audit |
|---|---|---|---|---|
| **`prototype_train_sample_100k.csv`** | **99,919** | - `natural_train`: 80,000 rows<br>- `oversampled_train_anomaly`: 19,919 rows | - Natural spikes: 113 (0.141%)<br>- Oversampled spikes: 19,919 (100%)<br>- Total spikes: 20,032 (20.05%) | **PASSED ($A \cap B = \emptyset$):** 81 overlapping candidates removed; 0 duplicate rows. |
| **`natural_val_sample_20k.csv`** | **20,000** | - `natural_val`: 20,000 rows (un-oversampled) | - Natural spikes: **7** (**0.0350%**)<br>- Non-spikes: 19,993 (99.965%) | **PASSED:** Pure natural random sample mirroring validation base rate (~0.0315%). |
| **`natural_test_sample_20k.csv`** | **20,000** | - `natural_test`: 20,000 rows (un-oversampled) | - Natural spikes: **172** (**0.8600%**)<br>- Non-spikes: 19,828 (99.140%) | **PASSED:** Pure natural random sample mirroring test base rate (~0.7399%). |

> [!WARNING]
> **Validation Bench Statistical Limitation:** The presence of only 7 spike instances in the 20,000 natural validation sample limits statistical power for spike-specific evaluation in validation, but preserves natural out-of-time production distributions without artificial oversampling distortion.

### 5.2 Proposed FDI Score Distribution across Benches

| Evaluation Metric | Natural Train (80k) | Natural Val (20k) | Natural Test (20k) | Anomaly Train (19,919) |
|---|:---:|:---:|:---:|:---:|
| **Mean FDI Score** | 56.40 | 54.34 | 47.26 | **78.43** |
| **Median FDI Score** | 57.12 | 55.65 | 47.84 | **81.25** |
| **Low Risk ($0 - 29$)** | 7.12% | 6.88% | 16.38% | 0.00% |
| **Moderate Risk ($30 - 59$)** | 52.15% | 54.39% | 59.18% | 12.44% |
| **High Risk ($60 - 79$)** | 38.61% | 37.02% | 23.44% | 58.10% |
| **Critical Risk ($80 - 100$)** | 2.12% | 1.71% | 1.01% | **29.46%** |

### 5.3 Proposed FDI Independence from Price Spikes
- **Validation Bench:** Exactly **7,740 records** have $\text{FDI} \ge 60.0$ while `price_spike_flag == 0`.
- **Training Prototype:** Exactly **20,458 records** have $\text{FDI} \ge 60.0$ while `price_spike_flag == 0`.
- **Key Finding:** High FDI scores frequently occur in the complete absence of price spikes, commanded by reference anchor inflation ($MSRP > P_{\text{max,52}}$) and large discount inflation gaps. The 15% weight on price spikes does not dominate the score.

---

## 6. Unsupervised Isolation Forest Benchmark

The primary Isolation Forest was fitted **strictly on the 80,000 natural training rows** across the 6 continuous engineered features:

| Evaluation Bench | Sample Size | Mean Anomaly Score | Outlier Prediction Rate | Assessment |
|---|---|---|---|---|
| **Natural Validation Bench** | 20,000 rows | `+0.0457` | 13.32% (2,664 outliers) | Establishes inlier baseline under natural market conditions. |
| **Disjoint Anomaly Stress-Test** | 19,919 rows | `-0.0653` | Substantially more negative | Correctly isolates extreme pricing events with high sensitivity. |

> [!IMPORTANT]
> **Limitation & Integrity Statement:** Neither high FDI scores nor Isolation Forest outlier status represent legally verified fraud. They serve as complementary, explainable risk metrics identifying deceptive pricing dynamics. The methodology remains a proposed experimental approach pending formal team and faculty approval.

---

## 7. Known Limitations & Caveats

1. **Synthetic Nature of Dataset:** The data reflects simulated pricing behavior (Ornstein-Uhlenbeck processes with promotional overlays). Real-world retail anomalies may exhibit patterns not modeled in this simulation.
2. **Absence of Ground Truth Labels:** In the absence of positive `fake_discount_flag` records, the project must rely on heuristic and unsupervised methodologies rather than supervised classification.
3. **Absence of Seller Identifiers:** The dataset contains manufacturer `brand` (e.g., Apple, Google), but NO third-party seller or merchant ID. Rogue merchant tracking cannot be implemented.
4. **Validation Anomaly Sparsity:** The 20,000 natural validation bench contains only 7 price spikes. Future spike-specific evaluation should rely on the training anomaly stress-test set or the test split.
5. **Licence Harmonization:** Formal reconciliation between archive CC0 1.0 Universal and earlier recorded CC BY-SA 4.0 remains pending with the faculty mentor.
