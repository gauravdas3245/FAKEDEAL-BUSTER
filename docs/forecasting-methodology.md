# Conditional 14-day price forecasting

## Implemented method

`backend/app/services/forecast_service.py` operates on the actual read-only DuckDB observation history for one resolved product/platform and a strict `as_of` cutoff. It aggregates same-day records only when their prices are identical; conflicting same-day values fail instead of being averaged away. It requires 180 consecutive observed calendar days immediately before the analysis date. Missing or invalid observations are not forward-filled, interpolated, or synthesized.

Two simple baselines are tested: (1) repeat the last observed daily price, and (2) repeat the mean of the last seven observed daily prices. Five rolling-origin windows, each 14 days long and ordered chronologically, compare both methods using MAE and RMSE. The lower backtest RMSE is selected, with MAE as a tie-breaker. The returned 14 points are predictions from that flat baseline. The response includes the training observation count, reference date, both methods' metrics, and explicit limitations.

This is a conditional baseline forecast, not a trained forecasting model, price-drop probability, or guarantee. No uncertainty interval is calculated. The historical validation is per product at request time and does not establish general future accuracy. Source `target_price_7d` and `target_price_30d` columns are never used as live observations or forecast targets.

## API

- `POST /api/forecast` takes internal `product_id`, `platform`, and `as_of`.
- `POST /api/inspect` returns the same forecast under the outer `forecast` key after product resolution.
- The legacy `POST /api/analyze` response remains unchanged and continues returning `forecast: null` / `forecast_status: UNAVAILABLE`.
- Inadequate or gapped history returns `INSUFFICIENT_HISTORY` with a null forecast and reason.

For the current 2026 application date, the source's last observation was 2024-12-30, so this dataset cannot support a current-date forecast. Choose a historical analysis time whose preceding 180 days are complete to demonstrate the feature. Even then, the forecast predicts the following 14 dates after `as_of`.
