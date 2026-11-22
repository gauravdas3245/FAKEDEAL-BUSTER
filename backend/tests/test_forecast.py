from datetime import datetime, timedelta
from pathlib import Path

from app.services.forecast_service import ForecastService


class FakeHistory:
    dataset_path = Path("history.duckdb")

    def __init__(self, missing=None, trend=False):
        self.missing = missing
        self.trend = trend

    def _query(self, _sql, params):
        start = params[3].date()
        rows = []
        for offset in range(180):
            day = start + timedelta(days=offset)
            if day == self.missing:
                continue
            price = float(100 + offset if self.trend else 100)
            rows.append((day, price, price, 1))
        return rows


def test_forecast_emits_fourteen_points_and_chronological_comparison():
    service = ForecastService(FakeHistory(trend=True))
    result = service.forecast("P1", "amazon", datetime(2024, 7, 1))
    assert result["status"] == "AVAILABLE"
    assert len(result["points"]) == 14
    assert result["points"][0]["date"] == "2024-07-02"
    assert result["points"][-1]["date"] == "2024-07-15"
    assert result["backtest"]["method"].startswith("five chronological")
    assert result["backtest"]["metrics"]["last_observation"]["observations"] == 70
    assert result["method"] in {"last_observation", "trailing_7_day_mean"}
    assert "uncertainty interval" in result["limitations"]


def test_forecast_withholds_prediction_when_daily_history_has_a_gap():
    service = ForecastService(FakeHistory(missing=datetime(2024, 1, 10).date()))
    result = service.forecast("P1", "amazon", datetime(2024, 7, 1))
    assert result["status"] == "INSUFFICIENT_HISTORY"
    assert result["forecast"] is None
    assert "missing dates are not filled" in result["message"]
