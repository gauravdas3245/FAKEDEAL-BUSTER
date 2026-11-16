# Dataset Preprocessing Notes

## 1. Purpose

This document describes the planned preprocessing steps for the E-Commerce Product Price Tracker Dataset used in the FakeDeal Buster project.

The objective is to prepare reliable and consistent data for exploratory analysis, feature engineering, and machine learning experiments.

## 2. Dataset Source

- **Dataset:** E-Commerce Product Price Tracker Dataset
- **Author:** Amith Nair
- **Platform:** Kaggle
- **Source link:** https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset

## 3. Initial Data Inspection

The dataset will be inspected before preprocessing to understand:

- Number of rows and columns.
- Column names and data types.
- Missing values.
- Duplicate records.
- Unique products and platforms.
- Price and discount distributions.
- Date range and time-series coverage.
- Availability and distribution of target labels.

## 4. Planned Preprocessing Steps

### 4.1 Data Selection

Only relevant columns required for price analysis, discount analysis, and model development will be selected.

### 4.2 Missing Value Handling

Missing values will be identified and handled according to the importance and data type of each column.

### 4.3 Duplicate Removal

Duplicate records will be checked using appropriate product, platform, and timestamp combinations.

### 4.4 Data Type Conversion

Date, price, discount, and numerical columns will be converted into suitable data types.

### 4.5 Data Validation

The following checks will be performed:

- Prices must be non-negative.
- Discount percentages must be within a valid range.
- Dates must be valid.
- Original price and current price relationships will be examined.
- Product and platform identifiers will be checked for consistency.

## 5. Feature Engineering

Potential features include:

- Discount percentage.
- Price difference between original and current price.
- Historical average price.
- Minimum and maximum historical price.
- Price variation over time.
- Product and platform information.

Features will only be created when the required source data is available and valid.

## 6. Target Label Validation

The dataset contains fields such as `fake_discount_flag` and `price_spike_flag`.

Before supervised model training, the project team will verify:

- Whether the labels contain meaningful variation.
- How the labels were generated.
- Whether target information leaks into input features.
- Whether the labels are suitable for the intended prediction task.

No unverified label will be treated as ground truth.

## 7. Memory and Performance Considerations

The dataset is large. Therefore:

- The complete dataset will not be loaded into memory unnecessarily.
- Only required columns will be selected.
- Data will be processed in manageable chunks or filtered samples.
- DuckDB or Parquet may be used for efficient data handling.
- Large raw dataset files will not be uploaded to GitHub.

## 8. Data Splitting

If supervised learning is appropriate, training and testing data will be separated carefully.

For time-dependent data, chronological splitting will be preferred to avoid using future observations during training.

## 9. Tools and Libraries

- Python
- Pandas
- NumPy
- Scikit-learn
- DuckDB
- PyArrow / Parquet

## 10. Current Status

**Status:** Planned preprocessing workflow.

The actual preprocessing results, missing-value counts, duplicate counts, feature definitions, and final dataset size will be documented after the dataset inspection and validation stages.

This document will be updated as the project progresses.
