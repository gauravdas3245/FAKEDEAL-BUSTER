# FakeDeal Buster — Dataset Data Dictionary

> **Document Status:** OFFICIAL PRODUCTION DATASET SPECIFICATION  
> **Prepared by:** Data Preparation Analyst (Lakhyajyoti Phukan)  
> **Target Architecture:** 46 Original Raw Columns + 13 Prototype Feature Pipeline Columns = **59 Total Columns**

---

## 1. Governance, Licence & Scope Statement

### 1.1 Verified Dataset Scope
This data dictionary documents the complete schema for the *E-Commerce Product Price Tracker Dataset* (Amith Nair, Kaggle) utilized in the **FakeDeal Buster** academic project. It covers all 25,606,940 raw observation records across two full years (`2023-01-01` to `2024-12-30`) and details the 13 feature additions introduced during prototype feature engineering.

### 1.2 Licence Governance (Documented Discrepancy)
- **Observed Physical Archive Licence:** Inspection of `LICENSE.txt` and `README.md` at `C:\End Sem Project\archive (1)` confirms the official text is **CC0 1.0 Universal (Public Domain Dedication)**.
- **Repository Record:** Earlier project documentation (`README.md`, `dataset/README.md`, `docs/dataset-source.md`) noted **Kaggle Open License / CC BY-SA 4.0 (as confirmed by the project faculty mentor)**.
- **Status:** **Pending Faculty Mentor Harmonization.** Both licenses permit academic research, but CC0 1.0 Universal is the physical text in the downloaded archive. The official repository record has not been altered pending formal faculty direction.

---

## 2. Original Dataset Schema (46 Verified Columns)

All 46 columns below have been verified against all 6 tabular CSV files in the raw dataset (`ecommerce_processed.csv`, `ecommerce_train.csv`, `ecommerce_val.csv`, `ecommerce_test.csv`, `ecommerce_forecast.csv`, `ecommerce_anomalies.csv`) and match `metadata.json` 100% in sequential column order and data types.

> [!NOTE]
> **Nomenclature Correction:** Physical CSV headers confirm the column name is **`title`** (correcting earlier references to `product_title`).

| # | Column Name | Raw Data Type | Feature Group | Project Role | Description & Verified Value Domain |
|---|---|---|---|---|---|
| 01 | `product_id` | String | Core Identifier | Product Key | Unique catalog identifier (e.g., `P0000001` to `P0010000`). Exactly 10,000 unique catalog items. |
| 02 | `title` | String | Core Identifier | Display Text | Product title string (e.g., `Google Max Smartphones  (Green)`). |
| 03 | `brand` | String | Categorical | Brand Metadata | Product manufacturer brand (e.g., `Google`, `Nike`, `Apple`, `Sony`). **Domain Note:** Represents the product manufacturer, NOT a third-party marketplace seller. |
| 04 | `category` | String | Categorical | Segmentation | Main retail category. Exactly 7 values: `Electronics` (25%), `Fashion` (20%), `Gaming` (15%), `Appliances` (12%), `Books` (10%), `Household` (10%), `Sports` (8%). |
| 05 | `subcategory` | String | Categorical | Segmentation | Subcategory within main category. Exactly 35 distinct values (5 per main category). |
| 06 | `platform` | String | Categorical | Platform Context | Marketplace platform where price was observed. Exactly 5 values: `amazon`, `ebay`, `walmart`, `flipkart`, `bestbuy`. *(Architectural target: ~20% uniform distribution).* |
| 07 | `timestamp` | Datetime (ISO) | Temporal | Time-Series Index | Observation timestamp in ISO-8601 (`YYYY-MM-DDTHH:MM:SS`). Daily observations spanning `2023-01-01` to `2024-12-30`. |
| 08 | `year` | Float (Numeric) | Temporal | Calendar Feature | Calendar year observation (`2023.0` or `2024.0`). |
| 09 | `month` | Float (Numeric) | Temporal | Seasonality | Calendar month (`1.0` to `12.0`). |
| 10 | `day` | Float (Numeric) | Temporal | Calendar Feature | Day of the month (`1.0` to `31.0`). |
| 11 | `dayofweek` | Float (Numeric) | Temporal | Seasonality | Day of week index (`0.0` = Monday to `6.0` = Sunday). |
| 12 | `price` | Float (USD) | Core Pricing | Selling Price | Current daily transaction price in USD. Verified positive across all 25.6M rows (`price > 0`). |
| 13 | `original_price` | Float (USD) | Core Pricing | Anchor Price | Displayed reference MSRP / list price in USD. Verified positive and $\ge \text{price}$ across all 25.6M rows. |
| 14 | `discount_pct` | Float (%) | Core Pricing | Nominal Discount | Displayed nominal percentage discount: $\frac{\text{original\_price} - \text{price}}{\text{original\_price}} \times 100\%$. Domain: `[0.0, 90.0]`. |
| 15 | `stock_status` | String | Inventory | Context Feature | Inventory availability status: `in_stock` or `out_of_stock`. |
| 16 | `avg_rating` | Float | Engagement | Quality Signal | Customer average review rating. Domain: `[1.0, 5.0]`. |
| 17 | `review_count` | Float (Integer) | Engagement | Volume Signal | Total count of customer reviews. |
| 18 | `is_flagship` | Float (Binary) | Product Flag | Brand Tier | Flag indicating flagship tier product (`0.0` or `1.0`). |
| 19 | `launch_year` | Float (Numeric) | Lifecycle | Product Age | Launch year of the product model. |
| 20 | `asin` | String | Identifier | Catalog Hash | Platform catalog alphanumeric hash code (e.g., `5F2B9323C3`). |
| 21 | `price_change_abs` | Float (USD) | Rolling Lag | Differential | Daily absolute price difference: $P_t - P_{t-1}$. Null on Day 1 ($t=0$). |
| 22 | `price_change_pct` | Float (%) | Rolling Lag | Differential | Daily percentage price difference: $\frac{P_t - P_{t-1}}{P_{t-1}} \times 100\%$. Null on Day 1 ($t=0$). |
| 23 | `price_7d_avg` | Float (USD) | Rolling Baseline | Short-Term Mean | 7-day trailing rolling mean price ($\mu_7$). Fully saturated after Day 7. |
| 24 | `price_30d_avg` | Float (USD) | Rolling Baseline | Monthly Baseline | 30-day trailing rolling mean price ($\mu_{30}$). Primary benchmark for genuine discount calculation. Fully saturated after Day 30. |
| 25 | `price_7d_std` | Float | Rolling Variance | Short-Term Spread | 7-day trailing rolling price standard deviation ($\sigma_7$). Null on Day 1 ($t=0$). Fully saturated after Day 7. |
| 26 | `price_30d_std` | Float | Rolling Variance | Monthly Spread | 30-day trailing rolling price standard deviation ($\sigma_{30}$). Null on Day 1 ($t=0$). Fully saturated after Day 30. |
| 27 | `price_7d_min` | Float (USD) | Rolling Extrema | Short-Term Floor | 7-day trailing rolling minimum price. Fully saturated after Day 7. |
| 28 | `price_30d_min` | Float (USD) | Rolling Extrema | Monthly Floor | 30-day trailing rolling minimum price. Fully saturated after Day 30. |
| 29 | `price_7d_max` | Float (USD) | Rolling Extrema | Short-Term Peak | 7-day trailing rolling maximum price. Verified empirically to track preceding observations ($t-6$ to $t$). Fully saturated after Day 7. |
| 30 | `price_30d_max` | Float (USD) | Rolling Extrema | Monthly Peak | 30-day trailing rolling maximum price ($P_{\text{max,30}}$). Fully saturated after Day 30. |
| 31 | `price_52w_min` | Float (USD) | Rolling Extrema | Annual Floor | 52-week trailing rolling minimum price. **Lookback Note:** Saturated only after 364 days; early 2023 values represent expanding inception-to-date minima. |
| 32 | `price_52w_max` | Float (USD) | Rolling Extrema | Annual Ceiling | 52-week trailing rolling maximum price ($P_{\text{max,52}}$). **Lookback Note:** Saturated only after 364 days; early 2023 values represent expanding inception-to-date maxima. |
| 33 | `price_volatility_30d` | Float | Rolling Variance | Volatility Metric | **ORIGINAL RAW COLUMN.** Pre-normalized coefficient of variation: $\frac{\sigma_{30}}{\mu_{30}}$. Null on Day 1 ($t=0$). Fully saturated after Day 30. |
| 34 | `discount_vs_30d_avg` | Float (%) | Comparative | Discount Spread | Provided difference between displayed discount and 30-day average price baseline. |
| 35 | `is_all_time_low` | Float (Binary) | Rolling Flag | Extreme Event | Flag indicating current price is the all-time low to date (`0.0` or `1.0`). |
| 36 | `is_all_time_high` | Float (Binary) | Rolling Flag | Extreme Event | Flag indicating current price is the all-time high to date (`0.0` or `1.0`). |
| 37 | `popularity_score` | Float | Engagement | Popularity Signal | Composite product popularity score. |
| 38 | `fake_discount_flag` | Float (Binary) | Indicator Flag | **DEFUNCT TARGET** | **VERIFIED FACT:** Exactly 0 positive instances across all 25,606,940 records (100% zero). Cannot be used as a classification target. |
| 39 | `price_spike_flag` | Float (Binary) | Anomaly Flag | Spike Indicator | Algorithmic price spike indicator. Exactly 48,554 positive records across full dataset (0.1896% incidence). **Domain Note:** Reflects statistical price volatility, NOT verified retail fraud. |
| 40 | `is_black_friday_week` | Float (Binary) | Calendar Flag | Promotional Event | Indicator for Black Friday promotional period (`0.0` or `1.0`). |
| 41 | `is_holiday_season` | Float (Binary) | Calendar Flag | Seasonal Event | Indicator for Q4 holiday shopping season (`0.0` or `1.0`). |
| 42 | `is_weekend` | Float (Binary) | Calendar Flag | Day Pattern | Indicator for weekend observations (`0.0` or `1.0`). |
| 43 | `value_score` | Float | Quality | Consumer Metric | Composite consumer value score. |
| 44 | `target_price_7d` | Float (USD) | Future Target | **LEAKAGE TARGET** | Expected selling price in 7 days ($t+7$). **STRICTLY EXCLUDED** from model feature inputs. |
| 45 | `target_price_30d` | Float (USD) | Future Target | **LEAKAGE TARGET** | Expected selling price in 30 days ($t+30$). **STRICTLY EXCLUDED** from model feature inputs. |
| 46 | `target_price_direction_7d` | Float (Categorical) | Future Target | **LEAKAGE TARGET** | 7-day price direction (`-1.0` down, `0.0` flat, `1.0` up). **STRICTLY EXCLUDED** from model feature inputs. |

---

## 3. Added Columns in Stage 5 Prototyping (13 Columns)

The prototype feature pipeline (`ml/prototype_pipeline.py`) computes **exactly 13 new columns**, expanding the schema to **59 total columns** in `prototype_train_sample_100k.csv`, `natural_val_sample_20k.csv`, and `natural_test_sample_20k.csv`.

### 3.1 Newly Engineered Continuous Pricing Features (6 Columns)

| Column Name | Data Type | Mathematical Formula | Numerical Safeguard | Lookback Saturation | Purpose & Consumer Intelligence |
|---|---|---|---|---|---|
| `ratio_to_30d_avg` | Float | $\frac{\text{price}}{\max(\text{price\_30d\_avg}, \epsilon)}$ | $\epsilon = 10^{-6}$ | Saturated after Day 30 | Measures price level relative to monthly mean. Ratios $\ge 1.0$ indicate price is at or above recent historical reality. |
| `ratio_to_30d_max` | Float | $\frac{\text{price}}{\max(\text{price\_30d\_max}, \epsilon)}$ | $\epsilon = 10^{-6}$ | Saturated after Day 30 | Evaluates current price relative to monthly ceiling. |
| `msrp_inflation_ratio` | Float | $\frac{\text{original\_price}}{\max(\text{price\_52w\_max}, \epsilon)}$ | $\epsilon = 10^{-6}$ | Expanding in early 2023; fully saturated Day 365 | Evaluates reference anchor legitimacy. Ratios $> 1.0$ indicate the advertised MSRP exceeds the annual peak. |
| `real_discount_30d` | Float (%) | $\max\left(0.0, \frac{\text{price\_30d\_avg} - \text{price}}{\max(\text{price\_30d\_avg}, \epsilon)} \times 100\right)$ | $\epsilon = 10^{-6}$ | Saturated after Day 30 | True economic discount relative to preceding 30-day average. |
| `discount_inflation_gap` | Float (%) | $\text{discount\_pct} - \text{real\_discount\_30d}$ | None | Saturated after Day 30 | Difference between advertised marketing markdown and real economic savings. |
| `recent_7d_peak_ratio` | Float | $\max\left(0.0, \frac{\text{price\_7d\_max} - \text{price\_30d\_avg}}{\max(\text{price\_30d\_avg}, \epsilon)}\right)$ | $\epsilon = 10^{-6}$ | Saturated after Day 30 | Measures recent price elevation relative to monthly baseline prior to promotional event. |

### 3.2 Proposed Standardized FDI Sub-Scores (4 Columns)
All sub-scores are scaled from $0.0$ to $100.0$ and represent an **experimental methodology pending formal faculty sign-off**:

| Sub-Score Name | Data Type | Weight | Formula | Sub-Score Behavior |
|---|---|:---:|---|---|
| `fdi_sub_gap` | Float | **35%** | $\text{clip}\left(\frac{\text{discount\_inflation\_gap}}{50.0}, 0.0, 1.0\right) \times 100.0$ | Primary penalty on marketing discount spread. Saturates at 50% gap. |
| `fdi_sub_mean_ratio` | Float | **30%** | $\text{clip}\left(\frac{\text{ratio\_to\_30d\_avg} - 0.85}{0.30}, 0.0, 1.0\right) \times 100.0$ | Evaluates baseline deal depth. Genuine deep discounts ($<0.85$) score 0; prices $\ge 1.15$ score 100. |
| `fdi_sub_msrp_inflation` | Float | **20%** | $\text{clip}\left(\frac{\text{msrp\_inflation\_ratio} - 1.00}{0.25}, 0.0, 1.0\right) \times 100.0$ | Penalizes reference price inflation above annual high. Saturates at 25% inflation. |
| `fdi_sub_recent_anomaly` | Float | **15%** | $\text{clip}\left(0.60 \cdot (\text{price\_spike\_flag} \cdot 100) + 0.40 \cdot \left(\frac{\text{recent\_7d\_peak\_ratio}}{0.20} \cdot 100\right), 0.0, 100.0\right)$ | Blends observed price spike events and recent price surge intensity. |

### 3.3 Proposed Composite FDI Outputs (2 Columns)

| Output Name | Data Type | Formula / Logic | Domain Interpretation |
|---|---|---|---|
| `fdi_score` | Float | $\sum (w_i \cdot S_i) = 0.35 \cdot S_{\text{gap}} + 0.30 \cdot S_{\text{mean}} + 0.20 \cdot S_{\text{msrp}} + 0.15 \cdot S_{\text{anom}}$ | Continuous composite Fake Discount Index scaled from $0.0$ to $100.0$. |
| `fdi_risk_tier` | String | $\ge 80$: `Critical Risk`<br>$\ge 60$: `High Risk`<br>$\ge 30$: `Moderate Risk`<br>$< 30$: `Low Risk` | Categorical consumer risk tier. **Experimental working hypothesis**, not legal fraud adjudication. |

### 3.4 Sample Source Metadata Column (1 Column)

| Column Name | Data Type | Permitted Values | Purpose |
|---|---|---|---|
| `sample_source` | String | `natural_train`<br>`oversampled_train_anomaly`<br>`natural_val`<br>`natural_test` | Explicitly tags row origin to prevent mixing oversampled anomaly stress-test data with natural evaluation data. |

---

## 4. Isolation Forest Feature Space ($\mathbf{X}_{\text{IF}}$)

The primary unsupervised Isolation Forest model is trained **strictly on 6 continuous dimensions**:
$$\mathbf{X}_{\text{IF}} = [\text{ratio\_to\_30d\_avg}, \text{ratio\_to\_30d\_max}, \text{msrp\_inflation\_ratio}, \text{discount\_inflation_gap}, \text{price\_volatility\_30d}, \text{recent\_7d\_peak\_ratio}]$$

> [!NOTE]
> **Definitive Feature Accounting:**
> The 6 Isolation Forest inputs consist of **5 newly engineered continuous features** plus **1 pre-existing raw column** (`price_volatility_30d`). The FDI sub-scores, composite scores, categorical tiers, and `sample_source` are strictly excluded from the Isolation Forest input vector.

---

## 5. Summary of Domain Entity Rules

1. **`brand` Meaning:** Represents product manufacturing brand (e.g., Apple, Nike, Samsung). It is NOT a marketplace seller ID and cannot be penalized as a rogue merchant proxy.
2. **`platform` Meaning:** Represents the marketplace site (Amazon, eBay, Walmart, Flipkart, BestBuy). Pricing comparisons reflect platform-level pricing policies.
3. **`fake_discount_flag` Meaning:** Defunct indicator (100% zero). Cannot be used for supervised training.
4. **`price_spike_flag` Meaning:** Statistical anomaly indicator reflecting short-term volatility. Does not constitute verified fraud ground truth.
