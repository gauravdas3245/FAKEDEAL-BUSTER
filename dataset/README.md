
# Dataset Documentation

## 1. Dataset Information

**Dataset Name:** E-Commerce Product Price Tracker Dataset

**Author:** Amith Nair

**Source:** Kaggle

**Dataset Link:** https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset

**License:** Kaggle Open License / CC BY-SA 4.0 (as confirmed by the project faculty mentor)

## 2. Purpose of the Dataset

This dataset is used in FakeDeal Buster to study e-commerce product pricing patterns, discount percentages, and historical price behaviour.

It supports the development and evaluation of analytical methods for identifying potentially misleading artificial discounts.

## 3. Dataset Characteristics

According to the dataset documentation, it contains:

- Approximately 25.6 million records.
- Around 10,000 products.
- Five e-commerce platforms.
- Seven product categories.
- Simulated daily price observations covering 2023–2024.

The dataset is synthetic and represents simulated retail pricing behaviour. It does not represent verified real-world marketplace transactions.

## 4. Data Usage in This Project

The dataset will be used for:

- Data inspection and quality analysis.
- Data cleaning and preprocessing.
- Product price and discount analysis.
- Feature engineering.
- Model development and evaluation, subject to label validation.
- Historical price trend analysis, where sufficient observations are available.

## 5. Important Data Considerations

- Dataset labels must be inspected before supervised model training.
- A label should not be treated as reliable ground truth without validation.
- An unusual price pattern does not automatically prove fraudulent activity.
- The full dataset is large and should be processed using memory-efficient methods.
- Only the required processed data and project-related documentation should be stored in this repository.

## 6. Data Access and Reproducibility

The original dataset is hosted on Kaggle. Users should obtain it from the original source and follow the applicable licence terms.

The raw dataset is not included in this GitHub repository because of its large size.

## 7. Attribution

E-Commerce Product Price Tracker Dataset by Amith Nair, hosted on Kaggle.

Dataset source: https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset

Accessed: 16-11-2026

Licence information recorded as confirmed by the project faculty mentor: Kaggle Open License / CC BY-SA 4.0.
