"""Build a compact, indexed runtime store from the approved Kaggle splits.

The raw files are read-only inputs. This command writes a separate DuckDB store
containing only application catalogue and historical price fields.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "derived" / "fakedeal_runtime.duckdb"
SPLITS = ("ecommerce_train.csv", "ecommerce_val.csv", "ecommerce_test.csv")
REQUIRED_COLUMNS = {
    "product_id", "title", "brand", "category", "subcategory", "platform",
    "timestamp", "price", "original_price", "discount_pct", "asin",
    "avg_rating", "review_count",
}


def sql_path(path: Path) -> str:
    return "'" + path.resolve().as_posix().replace("'", "''") + "'"


def build(data_root: Path, output: Path) -> dict:
    data_root = data_root.resolve()
    split_paths = [data_root / "data" / "splits" / name for name in SPLITS]
    missing = [str(path) for path in split_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required chronological dataset split(s) missing: " + ", ".join(missing))
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing runtime store: {output}")

    metadata_path = data_root / "metadata" / "metadata.json"
    source_metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
    expected_rows = source_metadata.get("row_count")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.with_name(output.stem + ".building.duckdb")
    if staging.exists():
        raise FileExistsError(f"Refusing to overwrite existing staging store: {staging}")

    con = duckdb.connect(str(staging))
    try:
        con.execute("SET preserve_insertion_order=false")
        con.execute("SET memory_limit='4GB'")
        con.execute("SET threads=4")
        paths_sql = "[" + ",".join(sql_path(path) for path in split_paths) + "]"
        schema = con.execute(
            f"DESCRIBE SELECT * FROM read_csv_auto({paths_sql}, union_by_name=true, sample_size=10000)"
        ).fetchall()
        columns = {row[0] for row in schema}
        if not REQUIRED_COLUMNS.issubset(columns):
            raise ValueError(f"Dataset is missing required application columns: {sorted(REQUIRED_COLUMNS - columns)}")

        selected = ", ".join(f'"{name}"' for name in sorted(REQUIRED_COLUMNS))
        con.execute(f"""
            CREATE TABLE observations AS
            SELECT {selected}
            FROM read_csv_auto({paths_sql}, union_by_name=true, sample_size=10000)
        """)
        row_count = con.execute("SELECT count(*) FROM observations").fetchone()[0]
        if expected_rows is not None and row_count != expected_rows:
            raise ValueError(f"Split row count {row_count} does not match source metadata {expected_rows}.")

        conflicts = con.execute("""
            SELECT count(*) FROM (
                SELECT product_id
                FROM observations
                GROUP BY product_id
                HAVING count(DISTINCT title) > 1
                    OR count(DISTINCT brand) > 1
                    OR count(DISTINCT category) > 1
                    OR count(DISTINCT subcategory) > 1
            )
        """).fetchone()[0]
        if conflicts:
            raise ValueError(f"Found {conflicts} product IDs with conflicting identity metadata; refusing unsafe catalogue creation.")

        duplicate = con.execute("""
            SELECT 1 FROM observations
            GROUP BY product_id, platform, timestamp
            HAVING count(*) > 1 LIMIT 1
        """).fetchone()
        if duplicate:
            raise ValueError("Source splits contain duplicate product/platform/timestamp keys; resolve conflicts before indexing.")

        con.execute("""
            CREATE TABLE products AS
            SELECT product_id, any_value(title) AS title, any_value(brand) AS brand,
                   any_value(category) AS category, any_value(subcategory) AS subcategory,
                   min(timestamp) AS first_observation, max(timestamp) AS last_observation
            FROM observations GROUP BY product_id
        """)
        con.execute("""
            CREATE TABLE product_platforms AS
            SELECT product_id, platform, any_value(asin) AS asin,
                   count(*) AS observation_count, min(timestamp) AS first_observation,
                   max(timestamp) AS last_observation
            FROM observations GROUP BY product_id, platform
        """)
        con.execute("CREATE INDEX observations_lookup_idx ON observations(product_id, platform, timestamp)")
        con.execute("CREATE INDEX products_name_idx ON products(title)")
        con.execute("CREATE INDEX product_platform_lookup_idx ON product_platforms(product_id, platform)")

        metrics = con.execute("""
            SELECT count(DISTINCT product_id), count(DISTINCT platform), count(DISTINCT category),
                   min(timestamp), max(timestamp)
            FROM observations
        """).fetchone()
        categories = [row[0] for row in con.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()]
        platforms = [row[0] for row in con.execute("SELECT DISTINCT platform FROM product_platforms ORDER BY platform").fetchall()]
        con.execute("CREATE TABLE store_metadata (key VARCHAR PRIMARY KEY, value VARCHAR)")
        metadata = {
            "source_root": str(data_root),
            "source_dataset": source_metadata.get("dataset_name", "Ecommerce Product Price Tracker Dataset"),
            "source_version": source_metadata.get("version"),
            "source_files": json.dumps([{"name": p.name, "size_bytes": p.stat().st_size} for p in split_paths]),
            "row_count": str(row_count),
            "unique_product_ids": str(metrics[0]),
            "unique_platforms": json.dumps(platforms),
            "unique_categories": json.dumps(categories),
            "min_timestamp": str(metrics[3]),
            "max_timestamp": str(metrics[4]),
            "url_mapping_available": "true" if "product_url" in columns else "false",
            "seller_name_available": "true" if "seller_name" in columns else "false",
            "seller_rating_available": "true" if "seller_rating" in columns else "false",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        con.executemany("INSERT INTO store_metadata VALUES (?, ?)", list(metadata.items()))
        con.execute("CHECKPOINT")
    finally:
        con.close()

    if output.exists():
        raise FileExistsError(f"Runtime-store destination appeared during build; preserving it: {output}")
    os.rename(staging, output)
    result = {
        "output": str(output), "row_count": row_count,
        "unique_product_ids": metrics[0], "platforms": platforms,
        "categories": categories, "date_range": [str(metrics[3]), str(metrics[4])],
        "url_mapping_available": "product_url" in columns,
        "seller_name_available": "seller_name" in columns,
        "seller_rating_available": "seller_rating" in columns,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=os.getenv("FAKEDEAL_RAW_DATA_DIR"),
                        help="Read-only extracted Kaggle dataset directory containing data/splits")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.data_root is None:
        parser.error("provide --data-root or set FAKEDEAL_RAW_DATA_DIR")
    print(json.dumps(build(args.data_root, args.output), indent=2))


if __name__ == "__main__":
    main()
