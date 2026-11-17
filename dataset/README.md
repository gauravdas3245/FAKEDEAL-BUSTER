# FakeDeal Buster — Dataset Documentation & Resources

## 1. Dataset Information

- **Dataset Name:** E-Commerce Product Price Tracker Dataset
- **Author:** Amith Nair
- **Source:** Kaggle
- **Dataset Link:** https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset
- **Licence Harmonization Status:** **Pending Formal Faculty Review.** The downloaded archive metadata (`LICENSE.txt` and `README.md`) declares **CC0 1.0 Universal (Public Domain Dedication)**, whereas initial project notes recorded **Kaggle Open License / CC BY-SA 4.0**. Both licences permit academic research and educational publication. Until formal direction is issued by the faculty mentor, the licence status is marked as pending harmonization without unilateral confirmation.

## 2. Dataset Documentation Directory

| Document | Purpose | Scope |
|---|---|---|
| [data-dictionary.md](data-dictionary.md) | Official production schema and data dictionary | 46 raw columns + 13 prototype engineered features (59 columns total) |
| [validation-report.md](validation-report.md) | Comprehensive empirical quality and census validation report | 25,606,940 census records & split profile audits |
| [preprocessing-notes.md](preprocessing-notes.md) | Data cleaning, chronological split methodology, and sampling strategy | Preprocessing methodology & feature engineering |

## 3. Storage Architecture and Size Measurement Reconciliation

To prevent ambiguity between compressed archives, individual table exports, and total extracted directories, the dataset measurements are defined as follows:

- **Compressed Download Archive (`archive (1).zip`):** $4,479,917,715$ bytes = **4.48 GB** (decimal, $10^9$ bytes) / **4.17 GiB** (binary, $2^{30}$ bytes).
- **Total Extracted Folder Footprint (`archive (1)`):** $24,740,253,212$ bytes = **24.74 GB** (decimal) / **23.04 GiB** (binary) across all 7 extracted CSV files.
- **Full Census File (`ecommerce_processed.csv`):** $7,725,291,257$ bytes = **7.73 GB** (decimal) / **7.19 GiB** (binary). Earlier references to "7.7 GB" refer exclusively to this single consolidated file.
- **Partitioned Splits:**
  - `ecommerce_train.csv`: $15,649,576,022$ bytes = **15.65 GB** (decimal) / **14.57 GiB** (binary) (80% chronological train partition).
  - `ecommerce_val.csv`: $686,160,836$ bytes = **686.16 MB** (decimal) / **654.37 MiB** (binary) (10% validation split).
  - `ecommerce_test.csv`: $679,202,284$ bytes = **679.20 MB** (decimal) / **647.74 MiB** (binary) (10% test split).
  - `ecommerce_forecast.csv` & `ecommerce_anomalies.csv`: Remainder (~0.02 GB).

## 4. Purpose and Characteristics

The dataset supports FakeDeal Buster by simulating daily retail price fluctuations across 2023–2024 to enable the study of price trends, discount inflation gaps, and reference price behavior.

- **Total Observations:** 25,606,940 rows across 730 consecutive calendar days.
- **Unique Catalog Products:** 10,000 unique catalog items.
- **Marketplace Platforms (5):** `amazon`, `bestbuy`, `ebay`, `flipkart`, `walmart`.
- **Main Categories (7):** `Electronics`, `Fashion`, `Gaming`, `Appliances`, `Books`, `Household`, `Sports`.
- **Subcategories:** 35 distinct subcategories (5 per category).

## 5. Storage and Access Rules

- **Raw Dataset Exclusion:** Due to file size (24.74 GB total extracted), raw dataset files are stored in external local directories and are strictly excluded from Git tracking via `.gitignore`.
- **Processed Samples:** Only compact representative evaluation samples and synthetic QA fixtures are stored in this repository.
