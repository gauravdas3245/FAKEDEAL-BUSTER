# FakeDeal Buster – Final Synchronized Dataset Preprocessing Notes

> **Document Status:** FINAL RECONCILED SPECIFICATION  
> **Prepared by:** Senior Data Engineer & ML Data Preparation Specialist (Lakhyajyoti Phukan)  
> **Audited for:** Gaurav Das (ML Developer) & Faculty Mentor  
> **Effective Date:** 2026-11-17  
> **Implementation Code:** `ml/prototype_pipeline.py`

---

## 1. Executive Preprocessing Status & Architecture

This document formalizes the complete data preparation and feature engineering methodology for the *E-Commerce Product Price Tracker Dataset*.

To ensure scientific reproducibility and maintain engineering boundaries, all operations are classified by verification status:

| Preprocessing Stage | Classification | Scope / Artifact | Verification Details |
|---|---|---|---|
| **Raw Dataset Discovery & Location** | **VERIFIED FACT** | `C:\End Sem Project\archive (1)` | 24.74 GB extracted (23.04 GiB), 25,606,940 records, 7 CSV files. |
| **Full Census & Quality Audit** | **VERIFIED FACT** | All 25.6M records | 0 missing values in core pricing, 0 negative prices, 0 duplicate keys. |
| **Chronological Split Integrity** | **VERIFIED FACT** | 80/10/10 time partition | Train (583d), Val (73d), Test (74d). 730 consecutive calendar days without overlap. |
| **Boundary Null Mitigation** | **VERIFIED FACT** | Cutoff `2023-01-31` | Day 1–30 warm-up truncation eliminates 86 lag initialization nulls in training. |
| **Feature Engineering Pipeline** | **VERIFIED FACT** | `ml/prototype_pipeline.py` | 6 continuous features, 4 FDI sub-scores, 2 composite outputs, 1 metadata column. |
| **Prototype Train Sample ($n=99,919$)** | **VERIFIED FACT** | `prototype_train_sample_100k.csv` | 80k natural + 19,919 disjoint anomalies ($A \cap B = \emptyset$). 59 columns. |
| **Natural Validation Bench ($n=20,000$)** | **VERIFIED FACT** | `natural_val_sample_20k.csv` | 100% natural random sample, 7 spikes (0.0350%), 59 columns. |
| **Natural Test Sample ($n=20,000$)** | **VERIFIED FACT** | `natural_test_sample_20k.csv` | 100% natural random sample, 172 spikes (0.8600%), 59 columns. |
| **Isolation Forest Prototype** | **EXPERIMENTAL** | Fitted on 80k natural train | Evaluated on validation bench and anomaly stress set. |
| **Fake Discount Index (FDI)** | **EXPERIMENTAL** | Heuristic composite index | Working hypothesis pending formal team and faculty approval. |
| **Full-Dataset Batch Transformation** | **PENDING PRODUCTION** | 25.6M records | Batch Parquet/DuckDB conversion deferred to Production. |

---

## 2. Dataset Storage Architecture & Exact Inventory

Raw files reside in external local storage outside Git tracking:

```
C:\End Sem Project\archive (1)\
├── data\
│   ├── full\
│   │   └── ecommerce_full.csv\ecommerce_processed.csv (8,266,972,621 bytes | 8.27 GB dec | 7.70 GiB bin | 25,606,940 rows)
│   ├── splits\
│   │   ├── ecommerce_train.csv (6,609,097,454 bytes | 6.61 GB dec | 6.16 GiB bin | 20,450,474 rows: 2023-01-01 to 2024-08-05)
│   │   ├── ecommerce_val.csv   (  825,896,977 bytes | 0.83 GB dec | 0.77 GiB bin |  2,560,694 rows: 2024-08-06 to 2024-10-17)
│   │   └── ecommerce_test.csv  (  831,979,063 bytes | 0.83 GB dec | 0.77 GiB bin |  2,595,772 rows: 2024-10-18 to 2024-12-30)
│   └── subsets\
│       ├── ecommerce_forecast.csv       (8,190,424,833 bytes | 8.19 GB dec | 7.63 GiB bin | 25,356,940 rows: 2023-01-01 to 2024-12-23)
│       ├── ecommerce_anomalies.csv      (   15,853,671 bytes | 15.85 MB dec| 15.12 MiB bin|     48,554 rows: price_spike_flag == 1.0)
│       └── ecommerce_recommendation.csv (        5,780 bytes |  5.78 KB dec|  5.64 KiB bin|        100 catalog summary rows)
```

- **Total Extracted Dataset:** 24,740,230,399 bytes across 7 CSV data files (24.7402 GB decimal / 23.0411 GiB binary; 24,740,253,212 bytes across all 11 extracted directory items).
- **Compressed Zip Archive:** 4,479,917,715 bytes (`archive (1).zip`: 4.48 GB decimal / 4.1722 GiB binary; reconciles earlier draft estimate of 4,475,346,654 bytes).
- **Exact Split Arithmetic:** $20,450,474 \text{ (train)} + 2,560,694 \text{ (val)} + 2,595,772 \text{ (test)} = \mathbf{25,606,940 \text{ rows}}$.

---

## 3. Memory-Safe Streaming Processing Pipeline

- **Memory Constraints:** Materializing 25.6M rows into a standard Pandas DataFrame requires $>16$ GB RAM, resulting in immediate Out-of-Memory (OOM) termination on development workstations.
- **Implemented Streaming Solution:**
  - Written in Python standard library (`csv`, `pathlib`, `sys`) with 64 KB streaming buffers.
  - Streaming throughput: ~430,000 to ~470,000 rows per second.
  - Active RAM footprint: Constant $< 50$ MB RAM across the entire scan.
  - Deterministic reservoir sampling (Seed = `42`) guarantees exact mathematical reproducibility without memory materialization.

---

## 4. Chronological Integrity & Split Contiguity

1. **Daily Granularity:** Every active `(product_id, platform)` pair contains uninterrupted daily records.
2. **Sequential Sorting:** Rows are stored in pre-sorted blocks grouped by product and platform, strictly advancing day-by-day. Zero out-of-order timestamps were detected across all 25.6M records.
3. **Contiguous Splits:**
   - Train ends on `2024-08-05T00:00:00`.
   - Validation begins on `2024-08-06T00:00:00` (Day 584, $\Delta t = +1$ day).
   - Test begins on `2024-10-18T00:00:00` (Day 657, $\Delta t = +1$ day).
   - **Zero observation overlap exists between splits.**

---

## 5. Duplicate Detection & Disjointness Enforcement

1. **Composite Key Uniqueness in Raw Data:**
   - Evaluated composite key: `(product_id, platform, timestamp)`.
   - Result: Exactly 0 duplicate records exist in the raw dataset.
2. **Prototype Disjointness Enforcement:**
   - In `ml/prototype_pipeline.py`, reservoir sampling drew 80,000 natural training rows and a candidate pool of 20,000 anomaly rows (`price_spike_flag == 1`).
   - Cross-partition deduplication identified that **81 candidate anomaly rows** were already selected in the natural sample.
   - The 81 overlapping rows were removed from the anomaly partition, yielding **19,919 net disjoint anomaly rows**.
   - Disjointness assertion: $\text{Natural Train} \cap \text{Anomaly Train} = \emptyset$ (0 duplicate rows). Total training prototype rows: $80,000 + 19,919 = \mathbf{99,919}$.

---

## 6. Rolling-Window Saturation & Warm-Up Cutoff

### 6.1 Training Split Initialization Nulls
In `ecommerce_train.csv` at $t=0$ (`2023-01-01`), exactly 86 observations contain empty strings for differential lag features (`price_change_abs`, `price_change_pct`, `price_7d_std`, `price_30d_std`, `price_volatility_30d`) due to absent prior-day history.
- **Rejected Solution:** Zero-imputation was explicitly rejected because assigning $\sigma = 0.0$ or $\text{CV} = 0.0$ creates an artificial signal of perfect price stability.
- **Implemented Solution:** Truncate the initial 30 days (`2023-01-01` to `2023-01-30`). Sampling begins strictly at `2023-01-31T00:00:00`.

### 6.2 Rolling-Window Saturation Analysis

| Feature Window | Columns Affected | Lookback Required | Behavior at Train Cutoff (`2023-01-31`) | Behavior at Validation / Test Time |
|---|---|---|---|---|
| **7-Day Rolling Features** | `price_7d_avg`, `std`, `min`, `max` | 7 days ($t-6$ to $t$) | **Fully saturated.** Lookback has 31 days of history. 0 nulls. | **Fully saturated.** Prior history $\gg 7$ days. |
| **30-Day Rolling Features** | `price_30d_avg`, `std`, `min`, `max`, `volatility_30d` | 30 days ($t-29$ to $t$) | **Fully saturated.** Lookback has exactly 30 days of prior history. 0 nulls. | **Fully saturated.** Prior history $\gg 30$ days. |
| **52-Week Rolling Features** | `price_52w_min`, `price_52w_max` | 364 days ($t-363$ to $t$) | **Expanding window.** On Day 31, only 31 days have elapsed. Values represent expanding inception-to-date extremes until Day 365 (`2023-12-31`). | **Fully saturated.** Validation (Day 584) and Test (Day 657) have $>364$ days of history. True 52-week windows. |

---

## 7. Feature Engineering Equations & Numerical Safeguards

```python
eps = 1e-6
safe_avg30 = max(price_30d_avg, eps)
safe_max30 = max(price_30d_max, eps)
safe_max52 = max(price_52w_max, eps)

# 1. Continuous Pricing Features (6 Columns)
ratio_to_30d_avg = price / safe_avg30
ratio_to_30d_max = price / safe_max30
msrp_inflation_ratio = original_price / safe_max52
real_discount_30d = max(0.0, (price_30d_avg - price) / safe_avg30 * 100.0)
discount_inflation_gap = discount_pct - real_discount_30d
recent_7d_peak_ratio = max(0.0, (price_7d_max - price_30d_avg) / safe_avg30)

# 2. Proposed FDI Sub-Scores (4 Columns, Clamped 0.0 - 100.0)
s_gap = clip(discount_inflation_gap / 50.0, 0.0, 1.0) * 100.0
s_mean = clip((ratio_to_30d_avg - 0.85) / 0.30, 0.0, 1.0) * 100.0
s_msrp = clip((msrp_inflation_ratio - 1.00) / 0.25, 0.0, 1.0) * 100.0
s_anom = clip(0.60 * (price_spike_flag * 100.0) + 0.40 * (recent_7d_peak_ratio / 0.20 * 100.0), 0.0, 100.0)

# 3. Illustrative Composite FDI Prototype Scoring (2 Columns)
# All calculated FDI scores represent illustrative prototype calculations evaluated on synthetic inputs.
# Thresholds (>=80 Critical, >=60 High, >=30 Moderate, <30 Low) are provisional heuristic bands.
# In live inference, uncomputable records or missing required inputs return INSUFFICIENT_INPUTS.
fdi_score = round(clip(0.35 * s_gap + 0.30 * s_mean + 0.20 * s_msrp + 0.15 * s_anom, 0.0, 100.0), 2)
if fdi_score >= 80.0:
    fdi_risk_tier = "Critical Risk"
elif fdi_score >= 60.0:
    fdi_risk_tier = "High Risk"
elif fdi_score >= 30.0:
    fdi_risk_tier = "Moderate Risk"
else:
    fdi_risk_tier = "Low Risk" 
```

### Feature Architecture & Model Space Delineation:

1. **Category A: 46 Raw Original Attributes:**
   Columns 1–46 from the Kaggle dataset (`product_id` to `target_price_direction_7d`).
2. **Category B: 13 Prototype Engineered Columns:**
   6 continuous pricing dimensions, 4 provisional FDI sub-scores, 2 composite scoring outputs, and 1 sample metadata tracking column (`sample_source` verified at Column #47; `evaluation_timestamp` confirmed absent).
3. **Category C: Four Canonical Isolation Forest Features (Verification & Status):**
   - **`msrp_to_30d_avg`:** **UNRESOLVED DISCREPANCY.** Implemented in prototype as `msrp_inflation_ratio = original_price / price_52w_max`. The feature `msrp_to_30d_avg` (MSRP / 30-day average) does not exist in `ml/prototype_pipeline.py`. Marked UNRESOLVED pending Gaurav's confirmation.
   - **`ratio_to_30d_avg`:** **VERIFIED IMPLEMENTED.** Present in `IF_FEATURES` (Line 41) as $P_t / \mu_{30}$.
   - **`price_volatility_30d`:** **VERIFIED IMPLEMENTED.** Original raw column (Column #33), consumed directly in `IF_FEATURES` (Line 45).
   - **`recent_7d_surge`:** **UNRESOLVED DISCREPANCY.** Implemented in prototype as `recent_7d_peak_ratio = (price_7d_max - price_30d_avg) / price_30d_avg`. The name `recent_7d_surge` does not exist in source code. Marked UNRESOLVED pending Gaurav's confirmation.
   *(Note: Prototype pipeline `ml/prototype_pipeline.py#L40-47` currently fits Isolation Forest on 6 continuous dimensions: `ratio_to_30d_avg`, `ratio_to_30d_max`, `msrp_inflation_ratio`, `discount_inflation_gap`, `price_volatility_30d`, `recent_7d_peak_ratio`).*

4. **Service Boundary Clarification (Prototype FDI vs. Backend Contracts):**
   - **Existing Pipeline Behaviour:** `compute_features_and_fdi` expects precomputed floats and raises standard `KeyError`/`TypeError` exceptions if inputs are missing. FDI scores represent illustrative prototype evaluations using provisional heuristic thresholds.
   - **Backend API Contract:** Responses such as `INSUFFICIENT_INPUTS`, `NEEDS_MORE_DATA`, and HTTP 422 are **PROPOSED QA TEST CONTRACTS** defined for future validation middleware, pending Rahul Amin's backend implementation in `backend/`.

---

## 8. Prototype Sample Demographics & Evaluation Sets

| Metric / Demographic | Prototype Train Sample (`prototype_train_sample_100k.csv`) | Natural Validation Bench (`natural_val_sample_20k.csv`) | Natural Test Sample (`natural_test_sample_20k.csv`) |
|---|:---:|:---:|:---:|
| **Output File Path** | `dataset/samples/` | `dataset/samples/` | `dataset/samples/` |
| **Total Row Count** | **99,919** | **20,000** | **20,000** |
| **Total Column Count** | **59 columns** | **59 columns** | **59 columns** |
| **File Size on Disk** | 41.7 MB (41,749,425 bytes) | 8.2 MB (8,236,252 bytes) | 8.2 MB (8,213,177 bytes) |
| **Date Range** | `2023-01-31` to `2024-08-05` | `2024-08-06` to `2024-10-17` | `2024-10-18` to `2024-12-30` |
| **Sample Source Partition** | `natural_train` (80k) + `oversampled_train_anomaly` (19,919) | `natural_val` (20k) | `natural_test` (20k) |
| **Natural Spikes Observed** | 113 spikes (0.141% in natural 80k) | **7 spikes** (**0.0350%**) | **172 spikes** (**0.8600%**) |
| **Total Spikes in File** | 20,032 spikes (20.05%) | 7 spikes (0.0350%) | 172 spikes (0.8600%) |
| **Platform Breakdown** | eBay: 20.26%, Walmart: 20.15%, BestBuy: 20.08%, Flipkart: 19.84%, Amazon: 19.67% | BestBuy: 20.41%, eBay: 20.19%, Walmart: 20.15%, Amazon: 19.64%, Flipkart: 19.62% | Amazon: 20.24%, Walmart: 20.19%, eBay: 20.00%, Flipkart: 19.89%, BestBuy: 19.69% |
| **Mean FDI Score** | 56.40 (Natural) / 78.43 (Anomaly) | 54.34 | 47.26 |

---

## 9. Next Steps & Pending Authorizations

1. **Approval to Promote Drafts:** Await formal confirmation from Gaurav Das to promote these finalized notes and data dictionary into `dataset/`.
2. **Production Model Scale Decision:** Confirm whether the verified 99,919-row prototype is sufficient for baseline ML development or if a larger sub-sample extraction is required.
3. **Faculty Methodological Review:** Present the unsupervised FDI and Isolation Forest framework to the faculty mentor for formal academic sign-off.
