"""Strict, read-only historical observation access."""

import csv
import math
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import duckdb

from app.exceptions import DatasetUnavailableError, HistoryConflictError, ProductNotFoundError

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def resolve_database_path(configured_path: Optional[Path | str] = None) -> Path:
    """
    Resolve the primary database store with fallback precedence:
    1. Explicit configured_path parameter (if provided)
    2. FAKEDEAL_DATABASE_PATH environment variable (if set and file exists)
    3. Production 1.99 GB full DuckDB store (artifacts/derived/fakedeal_runtime.duckdb)
    4. Lightweight demonstration DuckDB store (artifacts/derived/fakedeal_demo.duckdb)
    5. Unit fixture CSV (artifacts/rahul_dataset_handoff/p0000001_all_splits.csv)
    """
    if configured_path:
        return Path(configured_path)

    env_path = os.getenv("FAKEDEAL_DATABASE_PATH")
    if env_path:
        candidate = Path(env_path)
        if candidate.is_file():
            return candidate

    runtime_db = REPOSITORY_ROOT / "artifacts" / "derived" / "fakedeal_runtime.duckdb"
    if runtime_db.is_file():
        return runtime_db

    demo_db = REPOSITORY_ROOT / "artifacts" / "derived" / "fakedeal_demo.duckdb"
    if demo_db.is_file():
        return demo_db

    sample_csv = REPOSITORY_ROOT / "artifacts" / "rahul_dataset_handoff" / "p0000001_all_splits.csv"
    if sample_csv.is_file():
        return sample_csv

    return demo_db


DEFAULT_DATASET_PATH = resolve_database_path()


class HistoryService:
    """Query the indexed derived store; CSV support is retained for focused unit fixtures."""

    def __init__(self, dataset_path: Optional[Path | str] = None):
        self.dataset_path = resolve_database_path(dataset_path)

    @staticmethod
    def _naive_utc(value: datetime) -> datetime:
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

    def _query(self, sql: str, params: list):
        if not self.dataset_path.is_file():
            raise DatasetUnavailableError()
        try:
            with duckdb.connect(str(self.dataset_path), read_only=True) as con:
                return con.execute(sql, params).fetchall()
        except duckdb.Error as exc:
            raise DatasetUnavailableError() from exc

    def lookup_history(self, product_id: str, platform: str, as_of: datetime) -> List[Dict[str, object]]:
        target_id, target_platform = product_id.strip().upper(), platform.strip().lower()
        cutoff = self._naive_utc(as_of)
        if self.dataset_path.suffix.casefold() != ".csv":
            exists = self._query("SELECT 1 FROM product_platforms WHERE product_id=? AND platform=? LIMIT 1", [target_id, target_platform])
            if not exists:
                raise ProductNotFoundError(f"No historical records found for product {target_id!r} on platform {target_platform!r}.")
            rows = self._query("""
                SELECT timestamp,price FROM observations
                WHERE product_id=? AND platform=? AND timestamp < ? ORDER BY timestamp
            """, [target_id, target_platform, cutoff])
        else:
            if not self.dataset_path.is_file():
                raise DatasetUnavailableError()
            rows = []
            found = False
            with self.dataset_path.open("r", encoding="utf-8", newline="") as stream:
                for row in csv.DictReader(stream):
                    if (row.get("product_id") or "").strip().upper() == target_id and (row.get("platform") or "").strip().lower() == target_platform:
                        found = True
                        try:
                            timestamp = self._naive_utc(datetime.fromisoformat(row["timestamp"].strip()))
                            price = float(row["price"])
                        except (KeyError, TypeError, ValueError, AttributeError):
                            continue
                        if timestamp < cutoff:
                            rows.append((timestamp, price))
            if not found:
                raise ProductNotFoundError()
        daily: dict[date, tuple[datetime, float]] = {}
        for timestamp, raw_price in rows:
            timestamp = self._naive_utc(timestamp) if timestamp.tzinfo else timestamp
            price = float(raw_price)
            if not math.isfinite(price) or price <= 0:
                continue
            key = timestamp.date()
            if key in daily and daily[key][1] != price:
                raise HistoryConflictError(f"Conflicting duplicate historical prices on {key} for this product and platform.")
            daily.setdefault(key, (timestamp, price))
        return [{"product_id": target_id, "platform": target_platform, "timestamp": ts, "price": price}
                for ts, price in sorted(daily.values())]

    def actual_history(self, product_id: str, platform: str, as_of: datetime, days: int = 365) -> list[dict]:
        """Return unmodified actual price points in the preceding interval, with strict cutoff."""
        cutoff = self._naive_utc(as_of)
        start = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        start -= timedelta(days=max(1, min(days, 3650)))
        rows = self._query("""
            SELECT timestamp,price FROM observations
            WHERE product_id=? AND platform=? AND timestamp >= ? AND timestamp < ?
            ORDER BY timestamp
        """, [product_id.strip().upper(), platform.strip().lower(), start, cutoff])
        return [{"timestamp": ts.isoformat(), "price": float(price)} for ts, price in rows
                if math.isfinite(float(price)) and float(price) > 0]

    def historical_summary(self, product_id: str, platform: str, as_of: datetime, days: int = 30) -> dict:
        cutoff = self._naive_utc(as_of)
        from datetime import timedelta
        start = cutoff - timedelta(days=max(1, min(days, 3650)))
        row = self._query("""
            SELECT count(*),avg(price),min(price),max(price)
            FROM observations WHERE product_id=? AND platform=? AND timestamp >= ? AND timestamp < ?
        """, [product_id.strip().upper(), platform.strip().lower(), start, cutoff])[0]
        return {"window_days": days, "observation_count": int(row[0]),
                "average_price": float(row[1]) if row[1] is not None else None,
                "minimum_price": float(row[2]) if row[2] is not None else None,
                "maximum_price": float(row[3]) if row[3] is not None else None}

    def cross_platform(self, product_id: str, as_of: datetime) -> list[dict]:
        cutoff = self._naive_utc(as_of)
        return [{"platform": platform, "price": float(price), "timestamp": ts.isoformat()}
                for platform, price, ts in self._query("""
                    SELECT platform,price,timestamp FROM observations o
                    WHERE product_id=? AND timestamp < ? AND timestamp=(
                        SELECT max(timestamp) FROM observations x WHERE x.product_id=o.product_id
                        AND x.platform=o.platform AND x.timestamp < ?)
                    ORDER BY platform
                """, [product_id.strip().upper(), cutoff, cutoff])]
