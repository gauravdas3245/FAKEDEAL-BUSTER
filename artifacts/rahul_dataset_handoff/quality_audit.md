# Dataset Quality Audit

All aggregate, null, duplicate, and price checks were run in DuckDB without loading full splits into Pandas.

## Split-level counts and price checks

| Split | Rows | Unique products | Platforms | Product/platform pairs | Min timestamp | Max timestamp | Duplicate keys | Excess duplicate rows |
|---|---:|---:|---:|---:|---|---|---:|---:|
| train | 20,450,474 | 9,980 | 5 | 35,078 | 2023-01-01 00:00:00 | 2024-08-05 00:00:00 | 0 | 0 |
| val | 2,560,694 | 9,980 | 5 | 35,078 | 2024-08-06 00:00:00 | 2024-10-17 00:00:00 | 0 | 0 |
| test | 2,595,772 | 9,980 | 5 | 35,078 | 2024-10-18 00:00:00 | 2024-12-30 00:00:00 | 0 | 0 |

### Price value anomalies

| Split | Column | Null | Zero | Negative | Non-finite |
|---|---|---:|---:|---:|---:|
| train | `price` | 0 | 0 | 0 | 0 |
| train | `original_price` | 0 | 0 | 0 | 0 |
| val | `price` | 0 | 0 | 0 | 0 |
| val | `original_price` | 0 | 0 | 0 | 0 |
| test | `price` | 0 | 0 | 0 | 0 |
| test | `original_price` | 0 | 0 | 0 | 0 |

## Missing values by column

### train

| Column | Null rows |
|---|---:|
| `product_id` | 0 |
| `title` | 0 |
| `brand` | 0 |
| `category` | 0 |
| `subcategory` | 0 |
| `platform` | 0 |
| `timestamp` | 0 |
| `year` | 0 |
| `month` | 0 |
| `day` | 0 |
| `dayofweek` | 0 |
| `price` | 0 |
| `original_price` | 0 |
| `discount_pct` | 0 |
| `stock_status` | 0 |
| `avg_rating` | 0 |
| `review_count` | 0 |
| `is_flagship` | 0 |
| `launch_year` | 0 |
| `asin` | 0 |
| `price_change_abs` | 35,078 |
| `price_change_pct` | 35,078 |
| `price_7d_avg` | 0 |
| `price_30d_avg` | 0 |
| `price_7d_std` | 35,078 |
| `price_30d_std` | 35,078 |
| `price_7d_min` | 0 |
| `price_30d_min` | 0 |
| `price_7d_max` | 0 |
| `price_30d_max` | 0 |
| `price_52w_min` | 0 |
| `price_52w_max` | 0 |
| `price_volatility_30d` | 35,078 |
| `discount_vs_30d_avg` | 0 |
| `is_all_time_low` | 0 |
| `is_all_time_high` | 0 |
| `popularity_score` | 0 |
| `fake_discount_flag` | 0 |
| `price_spike_flag` | 0 |
| `is_black_friday_week` | 0 |
| `is_holiday_season` | 0 |
| `is_weekend` | 0 |
| `value_score` | 0 |
| `target_price_7d` | 0 |
| `target_price_30d` | 0 |
| `target_price_direction_7d` | 0 |

### val

| Column | Null rows |
|---|---:|
| `product_id` | 0 |
| `title` | 0 |
| `brand` | 0 |
| `category` | 0 |
| `subcategory` | 0 |
| `platform` | 0 |
| `timestamp` | 0 |
| `year` | 0 |
| `month` | 0 |
| `day` | 0 |
| `dayofweek` | 0 |
| `price` | 0 |
| `original_price` | 0 |
| `discount_pct` | 0 |
| `stock_status` | 0 |
| `avg_rating` | 0 |
| `review_count` | 0 |
| `is_flagship` | 0 |
| `launch_year` | 0 |
| `asin` | 0 |
| `price_change_abs` | 0 |
| `price_change_pct` | 0 |
| `price_7d_avg` | 0 |
| `price_30d_avg` | 0 |
| `price_7d_std` | 0 |
| `price_30d_std` | 0 |
| `price_7d_min` | 0 |
| `price_30d_min` | 0 |
| `price_7d_max` | 0 |
| `price_30d_max` | 0 |
| `price_52w_min` | 0 |
| `price_52w_max` | 0 |
| `price_volatility_30d` | 0 |
| `discount_vs_30d_avg` | 0 |
| `is_all_time_low` | 0 |
| `is_all_time_high` | 0 |
| `popularity_score` | 0 |
| `fake_discount_flag` | 0 |
| `price_spike_flag` | 0 |
| `is_black_friday_week` | 0 |
| `is_holiday_season` | 0 |
| `is_weekend` | 0 |
| `value_score` | 0 |
| `target_price_7d` | 0 |
| `target_price_30d` | 0 |
| `target_price_direction_7d` | 0 |

### test

| Column | Null rows |
|---|---:|
| `product_id` | 0 |
| `title` | 0 |
| `brand` | 0 |
| `category` | 0 |
| `subcategory` | 0 |
| `platform` | 0 |
| `timestamp` | 0 |
| `year` | 0 |
| `month` | 0 |
| `day` | 0 |
| `dayofweek` | 0 |
| `price` | 0 |
| `original_price` | 0 |
| `discount_pct` | 0 |
| `stock_status` | 0 |
| `avg_rating` | 0 |
| `review_count` | 0 |
| `is_flagship` | 0 |
| `launch_year` | 0 |
| `asin` | 0 |
| `price_change_abs` | 0 |
| `price_change_pct` | 0 |
| `price_7d_avg` | 0 |
| `price_30d_avg` | 0 |
| `price_7d_std` | 0 |
| `price_30d_std` | 0 |
| `price_7d_min` | 0 |
| `price_30d_min` | 0 |
| `price_7d_max` | 0 |
| `price_30d_max` | 0 |
| `price_52w_min` | 0 |
| `price_52w_max` | 0 |
| `price_volatility_30d` | 0 |
| `discount_vs_30d_avg` | 0 |
| `is_all_time_low` | 0 |
| `is_all_time_high` | 0 |
| `popularity_score` | 0 |
| `fake_discount_flag` | 0 |
| `price_spike_flag` | 0 |
| `is_black_friday_week` | 0 |
| `is_holiday_season` | 0 |
| `is_weekend` | 0 |
| `value_score` | 0 |
| `target_price_7d` | 245,546 |
| `target_price_30d` | 1,052,340 |
| `target_price_direction_7d` | 0 |

## P0000001 coverage

Available platforms: `amazon`, `bestbuy`, `ebay`, `flipkart`.

### Records by split and platform

| Split | Platform | Records | First timestamp | Last timestamp | Distinct dates |
|---|---|---:|---|---|---:|
| test | amazon | 74 | 2024-10-18T00:00:00 | 2024-12-30T00:00:00 | 74 |
| test | bestbuy | 74 | 2024-10-18T00:00:00 | 2024-12-30T00:00:00 | 74 |
| test | ebay | 74 | 2024-10-18T00:00:00 | 2024-12-30T00:00:00 | 74 |
| test | flipkart | 74 | 2024-10-18T00:00:00 | 2024-12-30T00:00:00 | 74 |
| train | amazon | 583 | 2023-01-01T00:00:00 | 2024-08-05T00:00:00 | 583 |
| train | bestbuy | 583 | 2023-01-01T00:00:00 | 2024-08-05T00:00:00 | 583 |
| train | ebay | 583 | 2023-01-01T00:00:00 | 2024-08-05T00:00:00 | 583 |
| train | flipkart | 583 | 2023-01-01T00:00:00 | 2024-08-05T00:00:00 | 583 |
| validation | amazon | 73 | 2024-08-06T00:00:00 | 2024-10-17T00:00:00 | 73 |
| validation | bestbuy | 73 | 2024-08-06T00:00:00 | 2024-10-17T00:00:00 | 73 |
| validation | ebay | 73 | 2024-08-06T00:00:00 | 2024-10-17T00:00:00 | 73 |
| validation | flipkart | 73 | 2024-08-06T00:00:00 | 2024-10-17T00:00:00 | 73 |

### Per-platform series across all splits

| Platform | Records | First date | Last date | Distinct dates | Duplicate-date records | Missing dates within span |
|---|---:|---|---|---:|---:|---:|
| amazon | 730 | 2023-01-01 | 2024-12-30 | 730 | 0 | 0 |
| bestbuy | 730 | 2023-01-01 | 2024-12-30 | 730 | 0 | 0 |
| ebay | 730 | 2023-01-01 | 2024-12-30 | 730 | 0 | 0 |
| flipkart | 730 | 2023-01-01 | 2024-12-30 | 730 | 0 | 0 |

Duplicate `(product_id, platform, date)` groups for P0000001: 0.
