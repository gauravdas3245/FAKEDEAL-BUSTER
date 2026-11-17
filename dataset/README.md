# FakeDeal Buster — Dataset Documentation & Resources

## 1. Dataset Information

- **Dataset Name:** E-Commerce Product Price Tracker Dataset
- **Author:** Amith Nair
- **Source:** Kaggle
- **Dataset Link:** https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset
- **Licence Governance:** CC0 1.0 Universal (per physical archive `LICENSE.txt`) / Kaggle Open License / CC BY-SA 4.0 (as recorded in project documentation, pending faculty mentor harmonization).

## 2. Dataset Documentation Directory

| Document | Purpose | Scope |
|---|---|---|
| [dataset/data-dictionary.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/dataset/data-dictionary.md) | Official production schema and data dictionary | 46 raw columns + 13 prototype engineered features (59 columns total) |
| [dataset/validation-report.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/dataset/validation-report.md) | Comprehensive empirical quality and census validation report | 25,606,940 census records & split profile audits |
| [dataset/preprocessing-notes.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/dataset/preprocessing-notes.md) | Data cleaning, chronological split methodology, and sampling strategy | Preprocessing methodology & feature engineering |

## 3. Purpose and Characteristics

The dataset supports FakeDeal Buster by simulating daily retail price fluctuations across 2023–2024 to enable the study of price trends, discount inflation gaps, and reference price behavior.

- **Total Observations:** 25,606,940 rows across 730 consecutive calendar days.
- **Unique Catalog Products:** 10,000 unique catalog items.
- **Marketplace Platforms (5):** `amazon`, `bestbuy`, `ebay`, `flipkart`, `walmart`.
- **Main Categories (7):** `Electronics`, `Fashion`, `Gaming`, `Appliances`, `Books`, `Household`, `Sports`.
- **Subcategories:** 35 distinct subcategories (5 per category).

## 4. Storage and Access Rules

- **Raw Dataset Exclusion:** Due to file size (24.74 GB extracted), raw dataset files are stored in external local directories and are strictly excluded from Git tracking via `.gitignore`.
- **Processed Samples:** Only compact representative evaluation samples and synthetic QA fixtures are stored in this repository.
