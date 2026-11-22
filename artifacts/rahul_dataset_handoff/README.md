# Rahul Dataset Handoff

This package is a read-only extract and audit for backend integration. Original files remain at `C:\end sem project\archive (5)\data\splits`.

## Files

- `p0000001_all_splits.csv`: all P0000001 records, all observed platforms, all original columns plus appended `source_split`; 2,920 rows, 964,720 bytes.
- `schema_report.md`: actual 46-column names, DuckDB inferred types, role groupings, timestamp format, and feature source fields.
- `quality_audit.md`: per-split quality metrics, all null counts, price checks, duplicates, and P0000001 coverage.
- `manifest.json`: exact paths, sizes, source metadata, and export verification results.

## Backend use

Load the compact extract as a read-only historical source. Select history by the exact composite key **`(product_id, platform)`**, then sort by `timestamp` ascending before calculating features. Do not combine one platform's prices with another platform's history.

The source splits are strictly chronological: train precedes validation, which precedes test. `source_split` records each exported row as `train`, `validation`, or `test`. Use training observations to form earlier history for validation records; do not fit preprocessing on validation or test. Preserve the split boundary in any evaluation.

## Four feature inputs

The four-feature vector uses the following source fields and calculations:

- Current `price` and advertised `original_price` for the observation being analyzed.
- Its `product_id`, `platform`, and `timestamp` to retrieve the matching history and define the as-of time.
- Historical `price` and `timestamp` values for that same product/platform to calculate the trailing 30-day mean and sample standard deviation, plus trailing 7-day maximum.

- `msrp_to_30d_avg = original_price / historical_30d_avg`
- `ratio_to_30d_avg = price / historical_30d_avg`
- `price_volatility_30d = historical_30d_sample_std / historical_30d_avg`
- `recent_7d_surge = max(0, (historical_7d_max - historical_30d_avg) / historical_30d_avg)`

The calculations are strictly backward-looking and exclude the current observation. `discount_inflation_gap` is a separate auxiliary explanation value; do not append it to the Isolation Forest vector. Dataset-provided rolling columns are included for reference, but this project's feature pipeline recomputes from historical prices.

Do not interpolate, forward-fill, or otherwise manufacture missing historical prices. Missing dates remain missing observations. Do not use future targets (`target_price_7d`, `target_price_30d`, `target_price_direction_7d`) or labels (`fake_discount_flag`, `price_spike_flag`) as feature inputs or fake-discount ground truth.

## Insufficient history behavior

The current feature pipeline requires at least **14 valid historical observations within the preceding 30 calendar days**. Below that threshold it returns an `insufficient_history` result and does not manufacture features. The backend should map that state to its agreed `NEEDS_MORE_DATA` response. The exact API enum/casing remains an integration decision: current API documentation uses `Needs More Data`, while this handoff uses the requested symbolic state `NEEDS_MORE_DATA`.

## Verified facts and open points

- Verified: all splits have the same observed schema; full counts and time boundaries are in `quality_audit.md`.
- Verified: export is compared to source rows in both directions using DuckDB `EXCEPT ALL`; zero differences are required by the build script.
- Verified: P0000001 export retains every original source column and appends `source_split`.
- Assumption for backend integration: history lookup uses the composite key `(product_id, platform)` and sorts by timestamp.
- Unresolved: API verdict spelling, behavior when current `price` exceeds `original_price`, and whether history will come from this extract or another catalog store.

## Rebuild

From the repository root, run:

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\build_rahul_dataset_handoff.py --data-root "C:\end sem project\archive (5)"
```

The script uses DuckDB with a 1 GB memory cap, writes only under this output directory, and does not modify source CSVs.
