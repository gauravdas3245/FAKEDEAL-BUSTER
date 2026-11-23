# Dataset Schema Report

Source root: `C:\end sem project\archive (5)`

DuckDB detected 46 columns in each split. The types below are inferred from the CSV data by DuckDB.

| # | Column | DuckDB type |
|---:|---|---|
| 1 | `product_id` | `VARCHAR` |
| 2 | `title` | `VARCHAR` |
| 3 | `brand` | `VARCHAR` |
| 4 | `category` | `VARCHAR` |
| 5 | `subcategory` | `VARCHAR` |
| 6 | `platform` | `VARCHAR` |
| 7 | `timestamp` | `TIMESTAMP` |
| 8 | `year` | `DOUBLE` |
| 9 | `month` | `DOUBLE` |
| 10 | `day` | `DOUBLE` |
| 11 | `dayofweek` | `DOUBLE` |
| 12 | `price` | `DOUBLE` |
| 13 | `original_price` | `DOUBLE` |
| 14 | `discount_pct` | `DOUBLE` |
| 15 | `stock_status` | `VARCHAR` |
| 16 | `avg_rating` | `DOUBLE` |
| 17 | `review_count` | `DOUBLE` |
| 18 | `is_flagship` | `DOUBLE` |
| 19 | `launch_year` | `DOUBLE` |
| 20 | `asin` | `VARCHAR` |
| 21 | `price_change_abs` | `DOUBLE` |
| 22 | `price_change_pct` | `DOUBLE` |
| 23 | `price_7d_avg` | `DOUBLE` |
| 24 | `price_30d_avg` | `DOUBLE` |
| 25 | `price_7d_std` | `DOUBLE` |
| 26 | `price_30d_std` | `DOUBLE` |
| 27 | `price_7d_min` | `DOUBLE` |
| 28 | `price_30d_min` | `DOUBLE` |
| 29 | `price_7d_max` | `DOUBLE` |
| 30 | `price_30d_max` | `DOUBLE` |
| 31 | `price_52w_min` | `DOUBLE` |
| 32 | `price_52w_max` | `DOUBLE` |
| 33 | `price_volatility_30d` | `DOUBLE` |
| 34 | `discount_vs_30d_avg` | `DOUBLE` |
| 35 | `is_all_time_low` | `DOUBLE` |
| 36 | `is_all_time_high` | `DOUBLE` |
| 37 | `popularity_score` | `DOUBLE` |
| 38 | `fake_discount_flag` | `DOUBLE` |
| 39 | `price_spike_flag` | `DOUBLE` |
| 40 | `is_black_friday_week` | `DOUBLE` |
| 41 | `is_holiday_season` | `DOUBLE` |
| 42 | `is_weekend` | `DOUBLE` |
| 43 | `value_score` | `DOUBLE` |
| 44 | `target_price_7d` | `DOUBLE` |
| 45 | `target_price_30d` | `DOUBLE` |
| 46 | `target_price_direction_7d` | `DOUBLE` |

## Column roles verified from names and data dictionary

- **product_id:** `product_id`
- **platform:** `platform`
- **timestamp:** `timestamp`
- **current_price:** `price`
- **original_price:** `original_price`
- **30_day_statistics:** `price_30d_avg`, `price_30d_std`, `price_30d_min`, `price_30d_max`, `price_volatility_30d`, `discount_vs_30d_avg`
- **7_day_statistics:** `price_7d_avg`, `price_7d_std`, `price_7d_min`, `price_7d_max`
- **targets_and_labels:** `fake_discount_flag`, `price_spike_flag`, `target_price_7d`, `target_price_30d`, `target_price_direction_7d`

## Timestamp representation

DuckDB inferred `TIMESTAMP`. Raw CSV sample values: `2023-01-01T00:00:00`, `2023-01-02T00:00:00`, `2023-01-03T00:00:00`, `2023-01-04T00:00:00`, `2023-01-05T00:00:00`.
Raw textual pattern checked across every non-null timestamp: `YYYY-MM-DDTHH:MM:SS` (24-hour time, no timezone suffix). train: 0 mismatches, val: 0 mismatches, test: 0 mismatches.

## Feature input fields

The four pipeline features are recomputed from `product_id`, `platform`, `timestamp`, `price`, and `original_price` history. `price_30d_*` and `price_7d_*` are dataset-provided columns but are not substituted for the pipeline's strictly backward-looking window calculations.
`discount_inflation_gap` is auxiliary and is excluded from the Isolation Forest vector.
