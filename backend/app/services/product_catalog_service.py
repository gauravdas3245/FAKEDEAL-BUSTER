"""Fast catalogue lookup backed by the derived store or small explicit CSV fixtures."""

import csv
import re
from pathlib import Path
from typing import Any

import duckdb

from app.exceptions import ProductNotFoundError
from app.services.history_service import DEFAULT_DATASET_PATH, resolve_database_path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORE_PATH = DEFAULT_DATASET_PATH


def normalize_identity(value: str) -> str:
    return " ".join(re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE))


class ProductCatalogService:
    """Resolve exact normalized names against verified product/platform metadata."""

    def __init__(self, dataset_path: Path | str | None = None):
        self.dataset_path = resolve_database_path(dataset_path)
        self._rows: list[dict[str, str]] | None = None
        self._catalog: dict[str, Any] | None = None

    def _identities(self) -> list[dict[str, str]]:
        if self._rows is not None:
            return self._rows
        if not self.dataset_path.is_file():
            from app.exceptions import DatasetUnavailableError
            raise DatasetUnavailableError()
        if self.dataset_path.suffix.casefold() == ".csv":
            with self.dataset_path.open("r", encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            identities: dict[tuple[str, str], dict[str, str]] = {}
            for row in rows:
                pid = (row.get("product_id") or "").strip().upper()
                platform = (row.get("platform") or "").strip().casefold()
                if not pid or not platform:
                    continue
                identities[(pid, platform)] = {
                    "product_id": pid, "title": (row.get("title") or "").strip(),
                    "brand": (row.get("brand") or "").strip(), "category": (row.get("category") or "").strip(),
                    "subcategory": (row.get("subcategory") or "").strip(), "platform": platform,
                    "asin": (row.get("asin") or "").strip(),
                }
            self._rows = list(identities.values())
            self._fixture_dates = [r.get("timestamp", "") for r in rows if r.get("timestamp")]
            return self._rows
        try:
            con = duckdb.connect(str(self.dataset_path), read_only=True)
        except duckdb.Error as exc:
            from app.exceptions import DatasetUnavailableError
            raise DatasetUnavailableError() from exc
        try:
            self._rows = [dict(zip(("product_id", "title", "brand", "category", "subcategory", "platform", "asin"), row))
                          for row in con.execute("""
                              SELECT p.product_id,p.title,p.brand,p.category,p.subcategory,pp.platform,coalesce(pp.asin,'')
                              FROM products p JOIN product_platforms pp USING(product_id)
                              ORDER BY p.product_id,pp.platform
                          """).fetchall()]
            meta = dict(con.execute("SELECT key,value FROM store_metadata").fetchall())
            self._store_meta = meta
        except duckdb.Error as exc:
            from app.exceptions import DatasetUnavailableError
            raise DatasetUnavailableError() from exc
        finally:
            con.close()
        return self._rows

    def catalog(self) -> dict[str, Any]:
        if self._catalog is not None:
            return self._catalog
        rows = self._identities()
        products: dict[tuple, dict[str, Any]] = {}
        for row in rows:
            key = (normalize_identity(row["title"]), row["category"], row["brand"], row["asin"])
            product = products.setdefault(key, {"title": row["title"], "brand": row["brand"],
                "category": row["category"], "subcategory": row["subcategory"], "asin": row["asin"], "platforms": []})
            if row["platform"] not in product["platforms"]:
                product["platforms"].append(row["platform"])
        meta = getattr(self, "_store_meta", {})
        dates = getattr(self, "_fixture_dates", [])
        self._catalog = {
            "products": list(products.values()),
            "platforms": sorted({r["platform"] for r in rows}),
            "categories": sorted({r["category"] for r in rows}),
            "category_platforms": [
                {"category": category, "platform": platform}
                for category, platform in sorted({(r["category"], r["platform"]) for r in rows})
            ],
            "date_range": {"start": meta.get("min_timestamp", "")[:10] or (min(dates)[:10] if dates else None),
                           "end": meta.get("max_timestamp", "")[:10] or (max(dates)[:10] if dates else None)},
            "url_mapping_supported": False,
            "amazon_asin_mapping_supported": any(r["platform"] == "amazon" and r["asin"] for r in rows),
            "product_count": len({r["product_id"] for r in rows}),
        }
        return self._catalog

    def search(self, query: str = "", category: str = "", platform: str = "", limit: int = 30) -> list[dict[str, Any]]:
        q, cat, plat = normalize_identity(query), normalize_identity(category), platform.casefold().strip()
        bounded_limit = max(1, min(limit, 100))
        if self.dataset_path.suffix.casefold() != ".csv":
            if not self.dataset_path.is_file():
                from app.exceptions import DatasetUnavailableError
                raise DatasetUnavailableError()
            try:
                with duckdb.connect(str(self.dataset_path), read_only=True) as con:
                    return [dict(zip(("product_id", "title", "brand", "category", "subcategory", "platform", "asin"), row))
                            for row in con.execute("""
                                SELECT p.product_id,p.title,p.brand,p.category,p.subcategory,pp.platform,coalesce(pp.asin,'')
                                FROM products p JOIN product_platforms pp USING(product_id)
                                WHERE (? = '' OR strpos(regexp_replace(lower(coalesce(p.title,'')), '[^a-z0-9]+', ' ', 'g'), ?) > 0
                                                OR strpos(regexp_replace(lower(coalesce(p.brand,'')), '[^a-z0-9]+', ' ', 'g'), ?) > 0)
                                  AND (? = '' OR lower(p.category) = ?)
                                  AND (? = '' OR lower(pp.platform) = ?)
                                ORDER BY p.title, p.brand, pp.platform, p.product_id LIMIT ?
                            """, [q, q, q, cat, cat, plat, plat, bounded_limit]).fetchall()]
            except duckdb.Error as exc:
                from app.exceptions import DatasetUnavailableError
                raise DatasetUnavailableError() from exc
        results = []
        seen = set()
        for row in self._identities():
            title, brand = normalize_identity(row["title"]), normalize_identity(row["brand"])
            if q and q not in title and q not in brand:
                continue
            if cat and normalize_identity(row["category"]) != cat:
                continue
            if plat and row["platform"] != plat:
                continue
            key = (row["product_id"], row["platform"])
            if key in seen:
                continue
            seen.add(key)
            results.append({k: row[k] for k in ("title", "brand", "category", "subcategory", "platform", "asin")})
            if len(results) >= bounded_limit:
                break
        return results

    def resolve(self, product_name: str, platform: str, category: str, selected_product_id: str | None = None) -> dict[str, Any]:
        rows = self._identities()
        name_key, category_key, platform_key = normalize_identity(product_name), normalize_identity(category), platform.strip().casefold()
        name_rows = [r for r in rows if normalize_identity(r["title"]) == name_key]
        if not name_rows:
            raise ProductNotFoundError("Historical data is unavailable for this product name.")
        category_rows = [r for r in name_rows if normalize_identity(r["category"]) == category_key]
        if not category_rows:
            raise ProductNotFoundError("This product name is not available in the selected category.")
        matches = [r for r in category_rows if r["platform"] == platform_key]
        if not matches:
            raise ProductNotFoundError("Historical data is unavailable for this product on the selected platform.")
        if selected_product_id:
            chosen = [r for r in matches if r["product_id"] == selected_product_id.strip().upper()]
            if len(chosen) != 1:
                raise ProductNotFoundError("The selected product match is no longer available.")
            return {"status": "RESOLVED", **chosen[0]}
        ids = {r["product_id"] for r in matches}
        if len(ids) == 1:
            return {"status": "RESOLVED", **matches[0]}
        candidates = [{k: next(r for r in matches if r["product_id"] == pid)[k]
                       for k in ("product_id", "title", "brand", "asin", "category", "subcategory", "platform")}
                      for pid in sorted(ids)]
        signatures = {(r["title"], r["brand"], r["asin"], r["category"], r["platform"]) for r in candidates}
        return {"status": "AMBIGUOUS_PRODUCT", "selection_possible": len(signatures) == len(candidates), "candidates": candidates}

    def resolve_asin(self, asin: str, platform: str = "amazon") -> list[dict[str, str]]:
        """Resolve an exact marketplace identifier from a supported dataset field."""
        token = asin.strip().upper()
        if not token or platform.casefold() != "amazon":
            return []
        return [row for row in self._identities()
                if row["platform"] == "amazon" and row["asin"].strip().upper() == token]

    def category_for(self, product_id: str, platform: str) -> str | None:
        """Look up one product category without loading observation history."""
        product_id, platform = product_id.strip().upper(), platform.strip().casefold()
        if self.dataset_path.suffix.casefold() == ".csv":
            return next((row["category"] for row in self._identities()
                         if row["product_id"] == product_id and row["platform"] == platform), None)
        if not self.dataset_path.is_file():
            return None
        try:
            with duckdb.connect(str(self.dataset_path), read_only=True) as connection:
                row = connection.execute("""
                    SELECT p.category FROM products p JOIN product_platforms pp USING(product_id)
                    WHERE p.product_id=? AND pp.platform=? LIMIT 1
                """, [product_id, platform]).fetchone()
            return str(row[0]) if row else None
        except duckdb.Error:
            return None
