# Supervised Model Comparison Report: Logistic Regression vs Random Forest

**Experiment Scope:** Held-Out Synthetic Test Data Only (N = 6,000)  
**Artifact Directory:** `artifacts/ml/synthetic_discount_v1/`  
**Dataset Bundle:** `artifacts/synthetic/discount_scenarios_v1/`  

> [!WARNING]
> **Academic Scope & Fraud Disclaimer:**  
> These metrics evaluate recovery of the generator's scenario rules under controlled synthetic distributions. They **must NOT be cited or claimed as real-world e-commerce fraud accuracy**, seller deception detection, or field performance. The original dataset does not contain verified fraud labels (`fake_discount_flag` has 0 positives across 25,606,940 records).

---

## 1. Executive Summary & Model Selection

A controlled supervised machine learning experiment was conducted to evaluate whether a linear baseline (Logistic Regression) or non-linear ensemble (Random Forest) better captures artificial reference-price inflation patterns when given identical feature representations.

### Selected Model: Random Forest
- **Selected Decision Threshold:** `0.4100` (tuned on the 6,000-row validation split)
- **Selection Rule:** Validation recall maximized subject to a strict false-positive rate constraint: $\text{FPR} \le 10\%$ on synthetic genuine discounts. Ties broken by PR-AUC and precision.
- **Why Random Forest was chosen:** Random Forest demonstrated superior discriminative power, achieving higher Recall (73.60% vs. 66.70%), higher Precision (89.54% vs. 87.99%), higher F1-score (0.8079 vs. 0.7588), higher ROC-AUC (0.9160 vs. 0.8891), higher PR-AUC (0.9308 vs. 0.9019), and a lower False-Positive Rate (8.60% vs. 9.10%) on the held-out test split.

---

## 2. Experimental Setup & Methodology

### Dataset Sizing and Splits
- **Total Generated Scenarios:** 40,000 balanced rows (50% Genuine Discount / 50% Artificially Inflated Reference Price).
- **Train Split (70%):** 28,000 rows (14,000 per class).
- **Validation Split (15%):** 6,000 rows (3,000 per class) — used exclusively for decision threshold tuning and model architecture selection.
- **Held-Out Test Split (15%):** 6,000 rows (3,000 per class) — evaluated strictly once for final reporting.
- **Split Integrity & Leakage Prevention:**
  - Independent stratified random splitting with fixed random seeds (`seed=20261118`).
  - No profile reuse: each synthetic observation is derived from a distinct sampled source profile.
  - Preprocessing pipelines (median imputation, one-hot encoding for platform/category, standard scaling for Logistic Regression) were fitted **strictly on the training split only**.
  - All CSV files are verified by SHA-256 hashes recorded in `manifest.json`.

### Feature Set
Both models ingest the identical 7-feature input vector:
1. `msrp_to_30d_avg` (Continuous): Advertised original reference price relative to 30-day historical average.
2. `ratio_to_30d_avg` (Continuous): Current sale price relative to 30-day historical average.
3. `price_volatility_30d` (Continuous): Sample standard deviation relative to 30-day historical average.
4. `recent_7d_surge` (Continuous): Highest price observed in trailing 7 days above 30-day mean.
5. `advertised_discount_pct` (Continuous): Claimed discount percentage `(original_price - current_price) / original_price * 100`.
6. `platform` (Categorical): 5 marketplaces (Amazon, Best Buy, eBay, Flipkart, Walmart).
7. `category` (Categorical): 7 categories (Appliances, Books, Electronics, Fashion, Gaming, Household, Sports).

---

## 3. Held-Out Test Set Benchmark Results

Evaluated on 6,000 independent held-out test examples:

| Metric | Logistic Regression (Baseline) | Random Forest (Selected) | Absolute Delta | Relative Gain |
|---|---:|---:|---:|---:|
| **Optimal Decision Threshold** | `0.6800` | `0.4100` | — | Tuned on validation |
| **Precision** | `0.8799` (87.99%) | `0.8954` (89.54%) | +0.0155 | +1.76% |
| **Recall (Sensitivity)** | `0.6670` (66.70%) | `0.7360` (73.60%) | +0.0690 | +10.34% |
| **F1-Score** | `0.7588` | `0.8079` | +0.0491 | +6.47% |
| **ROC-AUC** | `0.8891` | `0.9160` | +0.0269 | +3.03% |
| **PR-AUC (Average Precision)** | `0.9019` | `0.9308` | +0.0289 | +3.20% |
| **Gini Coefficient ($2 \times \text{ROC-AUC} - 1$)** | `0.7782` | `0.8320` | +0.0538 | +6.91% |
| **False Positive Rate (on Genuine)** | `0.0910` (9.10%) | `0.0860` (8.60%) | -0.0050 | -5.49% (Lower is better) |
| **Test Set Support (N)** | 6,000 | 6,000 | — | 3,000 per class |

> [!NOTE]
> **Gini Clarification:**  
> The reported Gini coefficient is the model discriminative performance metric:  
> $$\text{Gini} = 2 \times \text{ROC-AUC} - 1$$  
> This is distinct from tree node splitting criterion Gini impurity ($1 - \sum p_i^2$).

---

## 4. Confusion Matrices (Held-Out Test N = 6,000)

Class 0: `SYNTHETIC_GENUINE_DISCOUNT` (3,000 test cases)  
Class 1: `SYNTHETIC_ARTIFICIALLY_INFLATED_DISCOUNT` (3,000 test cases)  

### Logistic Regression Confusion Matrix (Threshold = 0.6800)
- **True Negatives (TN):** `2,727` (Correctly classified genuine discounts)
- **False Positives (FP):** `273` (Genuine discounts flagged as inflated; FPR = 9.10%)
- **False Negatives (FN):** `999` (Inflated discounts missed)
- **True Positives (TP):** `2,001` (Correctly identified inflated discounts; Recall = 66.70%)

$$\begin{pmatrix} \text{TN}=2727 & \text{FP}=273 \\ \text{FN}=999 & \text{TP}=2001 \end{pmatrix}$$

### Random Forest Confusion Matrix (Threshold = 0.4100)
- **True Negatives (TN):** `2,742` (Correctly classified genuine discounts)
- **False Positives (FP):** `258` (Genuine discounts flagged as inflated; FPR = 8.60%)
- **False Negatives (FN):** `792` (Inflated discounts missed)
- **True Positives (TP):** `2,208` (Correctly identified inflated discounts; Recall = 73.60%)

$$\begin{pmatrix} \text{TN}=2742 & \text{FP}=258 \\ \text{FN}=792 & \text{TP}=2208 \end{pmatrix}$$

### Key Comparison Insights:
1. **False Negative Reduction:** Random Forest correctly recovered 207 additional artificially inflated discounts (`2,208` vs `2,001`), cutting false negatives from 999 down to 792 (a 20.7% reduction in missed deceptive scenarios).
2. **False Positive Control:** Despite capturing significantly more inflated scenarios, Random Forest maintained a lower false-positive rate on genuine discounts (8.60% vs. 9.10%), generating 15 fewer false alarms on genuine listings.
3. **Threshold Calibration:** The linear model required a conservative threshold (0.6800) to keep false positives under 10%, sacrificing substantial recall. Random Forest's non-linear decision surface allowed an operating point at 0.4100 with higher precision and recall simultaneously.

---

## 5. Artifact Verification & Reproducibility

The model comparison experiment artifacts are saved under `artifacts/ml/synthetic_discount_v1/`:
- `logistic_regression.joblib` (SHA-256 verified)
- `random_forest.joblib` (SHA-256 verified)
- `metadata.json` (model architecture, hyperparameters, feature names)
- `evaluation.json` (per-threshold curve data, validation and test metrics)
- `checksums.sha256`

To re-run validation of the saved artifacts:
```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts/validate_synthetic_classifier.py
```
To query via the backend REST API:
```http
GET /api/models/synthetic-comparison
```
Response status: HTTP 200 `status: "AVAILABLE"`, `selected_model: "random_forest"`.
