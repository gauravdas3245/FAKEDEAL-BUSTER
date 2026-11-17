# FakeDeal Buster — Dataset Documentation & Resources

## 1. Dataset Information

- **Dataset Name:** E-Commerce Product Price Tracker Dataset
- **Author:** Amith Nair
- **Source:** Kaggle
- **Dataset Link:** https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset
- **Licence Harmonization Status:** **Pending Formal Faculty Mentor Review.** The downloaded archive metadata (`LICENSE.txt` and `README.md`) declares **CC0 1.0 Universal (Public Domain Dedication)**, whereas initial project notes recorded **Kaggle Open License / CC BY-SA 4.0**. Both licences grant permission for academic research, analysis, and educational publication. Until formal direction is issued by the faculty mentor, the licence status is explicitly documented as pending harmonization without unilateral confirmation.

## 2. Dataset Documentation Directory

| Document | Purpose | Scope |
|---|---|---|
| [data-dictionary.md](data-dictionary.md) | Official production schema and data dictionary | 46 raw columns + 13 prototype engineered features (59 columns total) |
| [validation-report.md](validation-report.md) | Comprehensive empirical quality and census validation report | 25,606,940 census records & split profile audits |
| [preprocessing-notes.md](preprocessing-notes.md) | Data cleaning, chronological split methodology, and sampling strategy | Preprocessing methodology & feature engineering |

## 3. Storage Architecture and Dataset Size Reconciliation

To prevent ambiguity between compressed archives, individual split files, and total directory footprints, all measurements have been verified directly against local filesystem metadata (`2026-11-18` audit):

| Component / File Path | Exact Byte Size | Decimal (GB / MB) | Binary (GiB / MiB) | Verification Basis / Description | Status |
|---|---|---|---|---|:---:|
| **Downloaded Archive**<br>`C:\End Sem Project\archive (1).zip` | **4,479,917,715 B** | **4.48 GB** ($10^9$ B) | **4.17 GiB** ($2^{30}$ B) | Direct OS filesystem metadata audit. (Earlier note of `4,475,346,654 B` represents an unverified typographical variance of ~4.5 MB). | **VERIFIED FACT** |
| **Total Extracted Folder**<br>`C:\End Sem Project\archive (1)` | **24,740,253,212 B** | **24.7403 GB** | **23.0412 GiB** | Sum of all 11 extracted files on disk (7 CSV files + 4 metadata/supporting files). | **VERIFIED FACT** |
| **Total CSV Data Volume** | **24,740,230,399 B** | **24.7402 GB** | **23.0411 GiB** | Sum of all 7 extracted CSV data files. | **VERIFIED FACT** |
| **Consolidated Census File**<br>`...\data\full\ecommerce_full.csv\ecommerce_processed.csv` | **8,266,972,621 B** | **8.27 GB** | **7.70 GiB** | Full 25,606,940 unpartitioned census records. (Earlier reference to "7.7 GB" refers to this single table in binary GiB: $7.6992$ GiB). | **VERIFIED FACT** |
| **Training Split**<br>`...\data\splits\ecommerce_train.csv` | **6,609,097,454 B** | **6.61 GB** | **6.16 GiB** | 80% chronological train partition (583 calendar days). | **VERIFIED FACT** |
| **Validation Split**<br>`...\data\splits\ecommerce_val.csv` | **825,896,977 B** | **825.90 MB** | **787.64 MiB** | 10% chronological validation partition (73 calendar days). | **VERIFIED FACT** |
| **Test Split**<br>`...\data\splits\ecommerce_test.csv` | **831,979,063 B** | **831.98 MB** | **793.44 MiB** | 10% chronological test partition (74 calendar days). | **VERIFIED FACT** |
| **Forecast Subset**<br>`...\data\subsets\ecommerce_forecast.csv` | **8,190,424,833 B** | **8.19 GB** | **7.63 GiB** | Evaluative forecasting time-series subset. | **VERIFIED FACT** |
| **Anomalies Subset**<br>`...\data\subsets\ecommerce_anomalies.csv` | **15,853,671 B** | **15.85 MB** | **15.12 MiB** | Filtered synthetic anomaly subset (`price_spike_flag == 1`). | **VERIFIED FACT** |
| **Recommendations Subset**<br>`...\data\subsets\ecommerce_recommendation.csv` | **5,780 B** | **5.78 KB** | **5.64 KiB** | Aggregated product recommendation lookup table. | **VERIFIED FACT** |
| **Supporting / Metadata Files (4 files)**<br>`LICENSE.txt`, `README.md`, `metadata.json`, `demo.ipynb` | **22,813 B** | **22.81 KB** | **22.28 KiB** | Supporting repository metadata and documentation. | **VERIFIED FACT** |

> [!NOTE]
> **Resolution of Earlier Numerical Discrepancies:**  
> - **The "15.65 GB" vs "6.61 GB" Train Size:** Earlier draft text mistakenly estimated `ecommerce_train.csv` at ~15.65 GB by proportionally dividing total disk volume. Direct filesystem audit confirms `ecommerce_train.csv` is **6,609,097,454 bytes** (6.61 GB decimal / 6.16 GiB binary).
> - **The "7.7 GB" Figure:** Refers exclusively to `ecommerce_processed.csv` in binary gigabytes ($8,266,972,621 / 2^{30} = 7.6992\text{ GiB} \approx 7.7\text{ GiB}$), not the total dataset.
> - **The "24.74 GB" Figure:** Refers to the total extracted disk volume of all 7 CSV files combined ($24,740,230,399$ bytes decimal).

## 4. Purpose and Characteristics

The dataset supports FakeDeal Buster by simulating daily retail price fluctuations across 2023–2024 to enable the study of price trends, discount inflation gaps, and reference price behavior.

- **Total Observations:** 25,606,940 rows across 730 consecutive calendar days.
- **Unique Catalog Products:** 10,000 unique catalog items.
- **Marketplace Platforms (5):** `amazon`, `bestbuy`, `ebay`, `flipkart`, `walmart`.
- **Main Categories (7):** `Electronics`, `Fashion`, `Gaming`, `Appliances`, `Books`, `Household`, `Sports`.
- **Subcategories:** 35 distinct subcategories (5 per category).

## 5. Storage and Access Rules

- **Raw Dataset Exclusion:** Due to file size (24.74 GB total extracted volume), raw dataset files are stored in external local directories and are strictly excluded from Git tracking via `.gitignore`.
- **Processed Samples:** Only compact representative evaluation samples and synthetic QA fixtures are stored in this repository.
