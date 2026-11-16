
# FakeDeal Buster – Dataset Data Dictionary

## 1. Overview

This document describes the important fields available in the E-Commerce Product Price Tracker Dataset and explains their potential use in the FakeDeal Buster project.

The exact data types, missing values, and field availability must be confirmed during dataset inspection.

## 2. Product Information Fields

| Field | Description | Project Usage |
|---|---|---|
| `product_id` | Unique identifier of a product | Product identification |
| `product_title` | Product name or title, if available | Product display |
| `brand` | Product brand | Product information |
| `category` | Product category | Category-based analysis |
| `platform` | E-commerce platform name | Platform comparison |

## 3. Pricing Fields

| Field | Description | Project Usage |
|---|---|---|
| `price` | Current recorded product price | Price analysis |
| `original_price` | Recorded original or reference price | Discount calculation |
| `discount_pct` | Recorded discount percentage | Discount analysis |
| `timestamp` | Date and time of the price observation | Historical price analysis |

## 4. Historical and Statistical Fields

| Field | Description | Project Usage |
|---|---|---|
| Rolling price statistics | Historical price summaries, where available | Price trend analysis |
| Price-related historical features | Previous price behaviour, where available | Feature engineering |
| `target_price_7d` | Dataset-provided seven-day target price | Forecasting experiments |
| `target_price_30d` | Dataset-provided thirty-day target price | Forecasting experiments |
| `target_price_direction_7d` | Dataset-provided seven-day price direction | Price direction analysis |

The exact names of rolling statistical columns must be verified against the original dataset schema before implementation.

## 5. Dataset Indicator Fields

| Field | Description | Project Usage |
|---|---|---|
| `fake_discount_flag` | Dataset-provided indicator associated with fake discounts | Candidate classification target, subject to label validation |
| `price_spike_flag` | Dataset-provided indicator associated with price spikes | Price anomaly analysis |

These indicators must not automatically be treated as verified real-world fraud labels. Their distribution and generation methodology must be examined before model training.

## 6. Important Notes

- Field names in this document are based on the available dataset documentation and must be checked against the actual downloaded files.
- Some descriptions are conceptual and require schema-level verification.
- Missing or inconsistent values must be handled during preprocessing.
- Target variables must not be used as input features when doing so would cause data leakage.
- The project will document any changes to field names or feature definitions during implementation.

## 7. Data Dictionary Maintenance

This document will be updated after the dataset inspection and preprocessing stages. The final version should reflect the actual columns, data types, and feature transformations used by the application.
