"""Conservative 14-day price forecast with strict chronological backtesting.

The two candidates are flat last-observation and flat trailing-seven-observation
baselines. Forecasts are withheld unless the preceding 180 calendar days are
fully observed; missing days are never filled or interpolated.
"""

from datetime import date, datetime, timedelta, timezone
import math

from app.services.history_service import HistoryService
from app.exceptions import HistoryConflictError


class ForecastService:
    MIN_DAYS = 180
    BACKTEST_WINDOWS = 5
    HORIZON_DAYS = 14

    def __init__(self, history_service: HistoryService | None = None):
        self.history_service = history_service or HistoryService()

    @staticmethod
    def _naive_utc(value: datetime) -> datetime:
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

    def forecast(self, product_id: str, platform: str, as_of: datetime) -> dict:
        cutoff = self._naive_utc(as_of)
        end_date = cutoff.date() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.MIN_DAYS - 1)
        if self.history_service.dataset_path.suffix.casefold() == ".csv":
            rows = self.history_service.lookup_history(product_id, platform, cutoff)
            values = {row["timestamp"].date(): float(row["price"]) for row in rows}
        else:
            rows = self.history_service._query("""
                SELECT CAST(timestamp AS DATE), min(price), max(price), count(DISTINCT price)
                FROM observations
                WHERE product_id=? AND platform=? AND timestamp < ?
                  AND timestamp >= ? AND price > 0
                GROUP BY CAST(timestamp AS DATE) ORDER BY CAST(timestamp AS DATE)
            """, [product_id.strip().upper(), platform.strip().lower(), cutoff,
                  datetime.combine(start_date, datetime.min.time())])
            if any(int(distinct_count) > 1 for _, _, _, distinct_count in rows):
                raise HistoryConflictError("Conflicting observed prices prevent a reliable forecast.")
            values = {day: float(price) for day, price, _, _ in rows
                      if price is not None and math.isfinite(float(price))}

        expected_dates = [start_date + timedelta(days=index) for index in range(self.MIN_DAYS)]
        if any(day not in values for day in expected_dates):
            return {"status": "INSUFFICIENT_HISTORY", "forecast": None,
                    "message": f"A forecast requires {self.MIN_DAYS} consecutive observed daily prices immediately before the analysis date; missing dates are not filled."}
        series = [values[day] for day in expected_dates]
        if len(series) < self.MIN_DAYS or any(price <= 0 for price in series):
            return {"status": "INSUFFICIENT_HISTORY", "forecast": None,
                    "message": "The historical series does not meet the forecast data requirements."}

        errors = {"last_observation": [], "trailing_7_day_mean": []}
        n = len(series)
        for window in range(self.BACKTEST_WINDOWS, 0, -1):
            origin = n - window * self.HORIZON_DAYS
            actual = series[origin:origin + self.HORIZON_DAYS]
            last = series[origin - 1]
            trailing_mean = sum(series[origin - 7:origin]) / 7
            errors["last_observation"].extend([predicted - observed for observed in actual for predicted in [last]])
            errors["trailing_7_day_mean"].extend([predicted - observed for observed in actual for predicted in [trailing_mean]])

        metrics = {}
        for name, residuals in errors.items():
            metrics[name] = {
                "mae": round(sum(abs(error) for error in residuals) / len(residuals), 6),
                "rmse": round(math.sqrt(sum(error * error for error in residuals) / len(residuals)), 6),
                "observations": len(residuals),
            }
        selected = min(metrics, key=lambda name: (metrics[name]["rmse"], metrics[name]["mae"], name))
        predicted = series[-1] if selected == "last_observation" else sum(series[-7:]) / 7
        forecast_start = cutoff.date() + timedelta(days=1)
        points = [{"date": (forecast_start + timedelta(days=offset)).isoformat(),
                   "predicted_price": round(predicted, 2)} for offset in range(self.HORIZON_DAYS)]
        return {
            "status": "AVAILABLE", "method": selected, "horizon_days": self.HORIZON_DAYS,
            "training_observation_count": len(series), "reference_date": end_date.isoformat(),
            "points": points, "backtest": {"method": "five chronological rolling-origin windows",
                                            "horizon_days": self.HORIZON_DAYS, "metrics": metrics},
            "limitations": "Baseline forecast, not a guarantee. Historical validation does not establish future accuracy; no uncertainty interval is estimated.",
        }
