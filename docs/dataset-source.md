# FakeDeal Buster – Dataset Source and Attribution

## 1. Dataset Information

- **Dataset Name:** E-Commerce Product Price Tracker Dataset
- **Creator:** Amith Nair
- **Platform:** Kaggle
- **Source:** https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset
- **Access Date:** 16 November 2026
- **Licence (as confirmed by faculty mentor):** Kaggle Open License / CC BY-SA 4.0
- **Dataset Type:** Synthetic e-commerce product pricing data

## 2. Dataset Description

The project uses the approved E-Commerce Product Price Tracker Dataset to study product pricing patterns and advertised discounts across multiple e-commerce platforms.

The dataset represents simulated retail pricing behaviour. It is intended for analytical and educational use and should not be treated as a record of verified real-world marketplace transactions.

## 3. Dataset Characteristics

According to the dataset information:

- Approximately 25.6 million records.
- Approximately 10,000 products.
- 46 columns.
- Five e-commerce platforms: Amazon, eBay, Walmart, Flipkart and BestBuy.
- Seven product categories.
- Daily observations covering 2023–2024.

These figures describe the dataset as documented by its source and may be verified again during local inspection.

## 4. Relevant Data Fields

The dataset includes fields such as:

- `product_id`
- `product_title`
- `brand`
- `category`
- `platform`
- `timestamp`
- `price`
- `original_price`
- `discount_pct`
- `fake_discount_flag`
- `price_spike_flag`
- `target_price_7d`
- `target_price_30d`
- `target_price_direction_7d`

The exact column names and availability will be confirmed during data inspection.

## 5. Dataset Usage in the Project

The dataset will be used for:

1. Product price analysis.
2. Discount percentage examination.
3. Historical pricing pattern analysis.
4. Data cleaning and feature preparation.
5. Machine learning experimentation, subject to label validation.
6. Anomaly analysis where appropriate.

Only the required columns and manageable data samples will be processed during development.

## 6. Data Quality and Label Validation

Before supervised machine learning is performed, the team must verify the meaning, distribution and reliability of the available target labels.

A label must not be assumed valid merely because it exists in the dataset.

If the available labels are unsuitable for distinguishing genuine and potentially misleading discounts, the team will document this limitation and use an appropriate alternative analytical or anomaly-detection approach.

## 7. Limitations

- The dataset is synthetic and does not establish actual marketplace fraud.
- Model performance on synthetic data cannot be presented as verified real-world fraud detection accuracy.
- Historical price analysis depends on the availability and quality of product observations.
- Forecasting results must be evaluated against available historical data.
- The project does not guarantee live marketplace integration.

## 8. Attribution and Licence

Dataset attribution:

**E-Commerce Product Price Tracker Dataset** by **Amith Nair**, hosted on Kaggle.

Source: https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset

Licence: Kaggle Open License / CC BY-SA 4.0, as confirmed by the faculty mentor.

The project will retain appropriate dataset attribution and follow the applicable licence conditions.

## 9. Privacy and Safety

The project uses anonymised public e-commerce data. No live marketplace credentials or personal user information (PII) are used.

No private customer information is required for the project's intended analysis.
