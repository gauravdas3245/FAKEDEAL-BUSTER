# Day 1: Machine Learning Feasibility Decision Note

**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Stage:** Day 1 Supervised Learning Feasibility Determination  
**Date:** 16 November 2026 (Completed 17 November 2026 early hours)  
**Author:** Gaurav Das (Team Leader & ML Developer)  
**Faculty Mentor:** Mr. Nitish Kr. Sarma  

---

## 1. Executive Feasibility Finding

> [!IMPORTANT]
> **Definitive Decision:** **Supervised binary classification on `fake_discount_flag` is currently IMPOSSIBLE.**
> The team will **NOT** train Logistic Regression, Random Forest, or any supervised classifier on `fake_discount_flag` during Day 1 or Day 2 unless external verified labels or explicit mentor-approved ground truth is provided. No labels will be fabricated.

---

## 2. Empirical Evidence from Full Dataset Census

An exhaustive census of all three chronological splits in the approved E-Commerce Product Price Tracker Dataset was conducted on 16 November 2026 using DuckDB streaming queries:

- **Total Inspected Rows:** **25,606,940**
- **`fake_discount_flag == 1` (Positive instances):** **0 (0.0000%)**
- **`fake_discount_flag == 0` (Negative instances):** **25,606,940 (100.0000%)**
- **`fake_discount_flag` Null Count:** **0**

### Mathematical & Practical Consequences:
1. **Zero Target Variance:** A binary classification label with zero positive instances has zero variance ($Var(Y) = 0$).
2. **Degenerate Classifier:** Any supervised classification algorithm (Logistic Regression, Decision Trees, Random Forest, SVM, or Neural Networks) trained on this target will converge to a trivial degenerate constant function ($f(X) = 0$), achieving a misleading 100% accuracy while learning zero predictive features.
3. **Evaluation Metrics Collapse:** Precision, Recall, F1-Score, and ROC-AUC cannot be meaningfully computed (division by zero in Recall; undefined ROC curve).

---

## 3. Why `price_spike_flag` Cannot Be Used as a Substitute Target

The dataset contains a second binary indicator: `price_spike_flag`, which has 48,554 positive instances (0.1896% of the dataset). Substituting this column as the training label is rejected for the following technical reasons:

1. **Diametric Semantic Mismatch:**
   - **`price_spike_flag` (Supply-Side Anomaly):** Represents an acute upward jump in the actual selling price ($P_t \gg P_{t-1}$). The dataset author explicitly notes that price spikes model inventory stockouts (*"Stock influence: Availability affects short-term price spikes"*).
   - **Fake Discount (Deceptive Marketing Anomaly):** Represents an artificial markup of the advertised reference price ($\text{OriginalPrice}_t \gg \text{MedianPrice}$) right before a promotional discount, while the actual selling price remains flat or drops marginally.
2. **Severe Error Modes:**
   - Training a fake-discount detector on `price_spike_flag` would train the model to predict stock shortages.
   - It would yield massive false alarms during genuine supply crunches and completely fail to flag pre-sale original price markups.

---

## 4. What Is Required to Enable Supervised Classification?

Supervised learning for fake discount detection can only become feasible if one of the following two criteria is fulfilled:

1. **External Verified Real-World Dataset:**
   - A dataset containing verified, real-world e-commerce transactions with audited ground-truth labels of deceptive pricing (e.g. regulatory consumer protection enforcement actions or verified consumer watchdog price-tracker investigations).
2. **Explicit Mentor-Approved Heuristic Ground-Truth Generator:**
   - A deterministic, rule-based ground-truth labeling function agreed upon and signed off by Faculty Mentor Mr. Nitish Kr. Sarma (e.g. defining a fake discount as any observation where $\text{original\_price} \ge 1.20 \times \text{price\_30d\_median}$ AND $\text{current\_price} \ge 0.95 \times \text{price\_30d\_median}$).
   - *Note:* If a heuristic generator is used to generate the ground-truth labels, evaluating a supervised model on those labels merely evaluates how well the model approximates the heuristic formula, which is an artificial circularity that must be disclosed in the academic report.

---

## 5. Recommended Technical Pivot (Stage 2 Strategy)

In light of the verified evidence, the team will pivot the machine learning architecture to a two-tier hybrid system:

1. **Unsupervised Anomaly Detection (Isolation Forest):**
   - Train an Isolation Forest on engineered relative pricing features (e.g., ratio of current price to 30-day median, ratio of original price to 30-day min, trailing volatility).
   - This isolates statistical pricing anomalies without relying on artificial zero-variance labels.
2. **Deterministic Fake Discount Index (FDI) Scoring Engine:**
   - Construct a transparent, domain-grounded heuristic score ($0 - 100$) evaluating:
     - **Pre-Sale Reference Markup:** Degree to which advertised original price exceeds recent 30-day typical pricing.
     - **Discount Legitimacy:** Comparison of current selling price against trailing historical minimum.
     - **Perpetual Discount Penalty:** Penalty for products perpetually claiming deep discounts.
   - Map composite FDI scores into four standardized verdicts:
     - `Potential Fake Discount` (FDI $\ge 70$)
     - `Suspicious Pricing` (FDI $45 - 69$)
     - `No Strong Fake-Discount Signal` (FDI $< 45$)
     - `Needs More Data` (Insufficient historical points)

---

## 6. Mentor Guidance Required

The following question is formally escalated to Faculty Mentor **Mr. Nitish Kr. Sarma**:

> *"The approved E-Commerce Product Price Tracker Dataset contains 25,606,940 records, but an exhaustive census confirms that `fake_discount_flag` contains exactly 0 positive occurrences across the entire dataset. In our original PRD, we planned to compare Logistic Regression and Random Forest conditional on label validity.*  
> *Given that supervised classification is degenerate on zero-variance labels, does the faculty mentor formally approve our pivot to an Unsupervised Isolation Forest Anomaly Detector combined with a domain-grounded Fake Discount Index (FDI) heuristic scoring engine?"*
