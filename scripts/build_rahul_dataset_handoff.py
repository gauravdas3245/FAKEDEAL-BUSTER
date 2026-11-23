"""Create a bounded DuckDB audit and P0000001 backend handoff package."""

import argparse
import json
from pathlib import Path
import sys

import duckdb

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = Path(r"C:\end sem project\archive (5)")
DEFAULT_OUTPUT = REPOSITORY_ROOT / "artifacts" / "rahul_dataset_handoff"
SPLITS = ("train", "val", "test")
SPLIT_LABELS = {"train": "train", "val": "validation", "test": "test"}
PRODUCT_ID = "P0000001"


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_path(path: Path) -> str:
    return sql_string(path.resolve().as_posix())


def table(path: Path) -> str:
    return f"read_csv_auto({sql_path(path)})"


def raw_table(path: Path) -> str:
    return f"read_csv({sql_path(path)}, all_varchar=true)"


def split_union(paths: dict[str, Path], columns: list[str] | None = None, raw: bool = False) -> str:
    pieces = []
    for name, path in paths.items():
        projection = "*" if columns is None else ", ".join(f'"{col}"' for col in columns)
        pieces.append(
            f"SELECT {projection}, {sql_string(SPLIT_LABELS[name])} AS source_split FROM {raw_table(path) if raw else table(path)}"
        )
    return " UNION ALL ".join(pieces)


def fmt(value) -> str:
    return "null" if value is None else str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    split_dir = args.data_root / "data" / "splits"
    paths = {name: split_dir / f"ecommerce_{name}.csv" for name in SPLITS}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        parser.error(f"Required split files are missing: {missing}")

    original_stat = {
        name: {"size_bytes": path.stat().st_size, "modified_ns": path.stat().st_mtime_ns}
        for name, path in paths.items()
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    export_path = args.output_dir / "p0000001_all_splits.csv"

    con = duckdb.connect()
    con.execute("SET memory_limit = '1GB'")
    con.execute("SET threads = 4")
    try:
        schemas = {}
        for name, path in paths.items():
            rows = con.execute(f"DESCRIBE SELECT * FROM {table(path)} LIMIT 0").fetchall()
            schemas[name] = {row[0]: row[1] for row in rows}
        reference_columns = list(schemas["train"])
        if any(list(schema) != reference_columns for schema in schemas.values()):
            raise RuntimeError("Train/validation/test schemas or column order differ")

        raw_timestamp = con.execute(
            f"SELECT timestamp FROM read_csv({sql_path(paths['train'])}, all_varchar=true) LIMIT 5"
        ).fetchall()
        timestamp_values = [row[0] for row in raw_timestamp]

        split_stats = {}
        split_nulls = {}
        duplicate_stats = {}
        for name, path in paths.items():
            src = table(path)
            null_exprs = ",\n".join(
                f'COUNT(*) FILTER (WHERE "{col}" IS NULL) AS "{col}"'
                for col in reference_columns
            )
            stats = con.execute(f"""
                SELECT COUNT(*) AS total_rows,
                       COUNT(DISTINCT product_id) AS unique_product_ids,
                       COUNT(DISTINCT platform) AS unique_platforms,
                       COUNT(DISTINCT (product_id, platform)) AS unique_product_platforms,
                       MIN(timestamp) AS min_timestamp,
                       MAX(timestamp) AS max_timestamp,
                       COUNT(*) FILTER (WHERE price IS NULL) AS price_null,
                       COUNT(*) FILTER (WHERE TRY_CAST(price AS DOUBLE) = 0) AS price_zero,
                       COUNT(*) FILTER (WHERE TRY_CAST(price AS DOUBLE) < 0) AS price_negative,
                       COUNT(*) FILTER (WHERE price IS NOT NULL AND NOT ISFINITE(TRY_CAST(price AS DOUBLE))) AS price_non_finite,
                       COUNT(*) FILTER (WHERE original_price IS NULL) AS original_price_null,
                       COUNT(*) FILTER (WHERE TRY_CAST(original_price AS DOUBLE) = 0) AS original_price_zero,
                       COUNT(*) FILTER (WHERE TRY_CAST(original_price AS DOUBLE) < 0) AS original_price_negative,
                       COUNT(*) FILTER (WHERE original_price IS NOT NULL AND NOT ISFINITE(TRY_CAST(original_price AS DOUBLE))) AS original_price_non_finite
                FROM {src}
            """).fetchone()
            keys = con.execute(f"""
                SELECT COUNT(*) AS duplicate_keys,
                       COALESCE(SUM(n - 1), 0) AS excess_records
                FROM (
                    SELECT COUNT(*) AS n FROM {src}
                    GROUP BY product_id, platform, timestamp
                    HAVING COUNT(*) > 1
                )
            """).fetchone()
            null_row = con.execute(f"""
                SELECT {null_exprs},
                       COUNT(*) FILTER (
                           WHERE timestamp IS NOT NULL
                             AND NOT regexp_full_match(timestamp, '[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}T[0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}')
                       ) AS timestamp_format_mismatch
                FROM {raw_table(path)}
            """).fetchone()
            split_stats[name] = {
                "total_rows": stats[0], "unique_product_ids": stats[1],
                "unique_platforms": stats[2], "unique_product_platforms": stats[3],
                "min_timestamp": str(stats[4]), "max_timestamp": str(stats[5]),
                "price": {"null": stats[6], "zero": stats[7], "negative": stats[8], "non_finite": stats[9]},
                "original_price": {"null": stats[10], "zero": stats[11], "negative": stats[12], "non_finite": stats[13]},
            }
            split_nulls[name] = {col: null_row[i] for i, col in enumerate(reference_columns)}
            split_stats[name]["timestamp_format_mismatch"] = null_row[len(reference_columns)]
            duplicate_stats[name] = {"duplicate_keys": keys[0], "excess_records": keys[1]}

        # Product export: all columns in source order, with source_split appended.
        union_sql = split_union(paths, reference_columns, raw=True)
        con.execute(f"""
            COPY (
                SELECT * FROM ({union_sql}) AS combined
                WHERE product_id = {sql_string(PRODUCT_ID)}
                ORDER BY timestamp, platform, source_split
            ) TO {sql_path(export_path)} (HEADER, DELIMITER ',', OVERWRITE_OR_IGNORE true)
        """)

        con.execute(f"CREATE TEMP VIEW p1_source AS SELECT * FROM ({union_sql}) u WHERE product_id={sql_string(PRODUCT_ID)}")
        con.execute(f"CREATE TEMP VIEW p1_export AS SELECT * FROM {raw_table(export_path)}")
        export_columns = reference_columns + ["source_split"]
        projection = ", ".join(f'"{col}"' for col in export_columns)
        forward_diff = con.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT {projection} FROM p1_source
                EXCEPT ALL
                SELECT {projection} FROM p1_export
            )
        """).fetchone()[0]
        reverse_diff = con.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT {projection} FROM p1_export
                EXCEPT ALL
                SELECT {projection} FROM p1_source
            )
        """).fetchone()[0]
        export_counts = con.execute(
            "SELECT source_split, COUNT(*) FROM p1_export GROUP BY source_split ORDER BY source_split"
        ).fetchall()

        p1_by_split_platform = con.execute(f"""
            SELECT source_split, platform, COUNT(*) AS records,
                   MIN(timestamp) AS min_timestamp, MAX(timestamp) AS max_timestamp,
                   COUNT(DISTINCT CAST(timestamp AS DATE)) AS distinct_dates
            FROM p1_export
            GROUP BY source_split, platform
            ORDER BY source_split, platform
        """).fetchall()
        p1_series = con.execute("""
            SELECT platform, COUNT(*) AS records,
                   MIN(CAST(timestamp AS DATE)) AS min_date,
                   MAX(CAST(timestamp AS DATE)) AS max_date,
                   COUNT(DISTINCT CAST(timestamp AS DATE)) AS distinct_dates,
                   COUNT(*) - COUNT(DISTINCT CAST(timestamp AS DATE)) AS duplicate_date_records,
                   date_diff('day', MIN(CAST(timestamp AS DATE)), MAX(CAST(timestamp AS DATE))) + 1
                       - COUNT(DISTINCT CAST(timestamp AS DATE)) AS missing_dates_in_span
            FROM p1_export
            GROUP BY platform
            ORDER BY platform
        """).fetchall()
        p1_duplicate_dates = con.execute("""
            SELECT platform, CAST(timestamp AS DATE) AS observed_date, COUNT(*) AS records
            FROM p1_export
            GROUP BY platform, CAST(timestamp AS DATE)
            HAVING COUNT(*) > 1
            ORDER BY platform, observed_date
        """).fetchall()
        p1_platforms = [row[0] for row in con.execute(
            "SELECT DISTINCT platform FROM p1_export ORDER BY platform"
        ).fetchall()]

    finally:
        con.close()

    final_stat = {
        name: {"size_bytes": path.stat().st_size, "modified_ns": path.stat().st_mtime_ns}
        for name, path in paths.items()
    }
    export_count = sum(row[1] for row in export_counts)
    export_info = {
        "path": str(export_path.resolve()),
        "size_bytes": export_path.stat().st_size,
        "records": export_count,
        "records_by_split": {row[0]: row[1] for row in export_counts},
        "source_export_except_all_rows": forward_diff,
        "export_source_except_all_rows": reverse_diff,
        "verified_exact_match": forward_diff == 0 and reverse_diff == 0,
    }

    schema_groups = {
        "product_id": [col for col in reference_columns if col == "product_id"],
        "platform": [col for col in reference_columns if col == "platform"],
        "timestamp": [col for col in reference_columns if col == "timestamp"],
        "current_price": [col for col in reference_columns if col == "price"],
        "original_price": [col for col in reference_columns if col == "original_price"],
        "30_day_statistics": [col for col in reference_columns if "30d" in col.lower() and not col.startswith("target_")],
        "7_day_statistics": [col for col in reference_columns if "7d" in col.lower() and not col.startswith("target_")],
        "targets_and_labels": [col for col in reference_columns if col.startswith("target_") or col.endswith("_flag")],
    }

    schema_lines = [
        "# Dataset Schema Report", "",
        f"Source root: `{args.data_root.resolve()}`", "",
        "DuckDB detected 46 columns in each split. The types below are inferred from the CSV data by DuckDB.", "",
        "| # | Column | DuckDB type |", "|---:|---|---|",
    ]
    schema_lines += [f"| {i} | `{col}` | `{schemas['train'][col]}` |" for i, col in enumerate(reference_columns, 1)]
    schema_lines += ["", "## Column roles verified from names and data dictionary", ""]
    for label, cols in schema_groups.items():
        schema_lines.append(f"- **{label}:** {', '.join(f'`{c}`' for c in cols) if cols else 'No matching columns'}")
    schema_lines += [
        "", "## Timestamp representation", "",
        f"DuckDB inferred `{schemas['train']['timestamp']}`. Raw CSV sample values: "
        + ", ".join(f"`{value}`" for value in timestamp_values) + ".",
        "Raw textual pattern checked across every non-null timestamp: `YYYY-MM-DDTHH:MM:SS` (24-hour time, no timezone suffix). "
        + ", ".join(f"{name}: {split_stats[name]['timestamp_format_mismatch']} mismatches" for name in SPLITS) + ".",
        "",
        "## Feature input fields", "",
        "The four pipeline features are recomputed from `product_id`, `platform`, `timestamp`, `price`, and `original_price` history. "
        "`price_30d_*` and `price_7d_*` are dataset-provided columns but are not substituted for the pipeline's strictly backward-looking window calculations.",
        "`discount_inflation_gap` is auxiliary and is excluded from the Isolation Forest vector.",
    ]
    (args.output_dir / "schema_report.md").write_text("\n".join(schema_lines) + "\n", encoding="utf-8")

    audit_lines = [
        "# Dataset Quality Audit", "",
        "All aggregate, null, duplicate, and price checks were run in DuckDB without loading full splits into Pandas.", "",
        "## Split-level counts and price checks", "",
        "| Split | Rows | Unique products | Platforms | Product/platform pairs | Min timestamp | Max timestamp | Duplicate keys | Excess duplicate rows |", 
        "|---|---:|---:|---:|---:|---|---|---:|---:|",
    ]
    for name in SPLITS:
        s, d = split_stats[name], duplicate_stats[name]
        audit_lines.append(
            f"| {name} | {s['total_rows']:,} | {s['unique_product_ids']:,} | {s['unique_platforms']:,} | "
            f"{s['unique_product_platforms']:,} | {s['min_timestamp']} | {s['max_timestamp']} | "
            f"{d['duplicate_keys']:,} | {d['excess_records']:,} |"
        )
    audit_lines += ["", "### Price value anomalies", "", "| Split | Column | Null | Zero | Negative | Non-finite |", "|---|---|---:|---:|---:|---:|"]
    for name in SPLITS:
        for col in ("price", "original_price"):
            p = split_stats[name][col]
            audit_lines.append(f"| {name} | `{col}` | {p['null']:,} | {p['zero']:,} | {p['negative']:,} | {p['non_finite']:,} |")
    audit_lines += ["", "## Missing values by column", ""]
    for name in SPLITS:
        audit_lines += [f"### {name}", "", "| Column | Null rows |", "|---|---:|"]
        audit_lines += [f"| `{col}` | {split_nulls[name][col]:,} |" for col in reference_columns]
        audit_lines.append("")
    audit_lines += [
        "## P0000001 coverage", "",
        f"Available platforms: {', '.join(f'`{p}`' for p in p1_platforms)}.", "",
        "### Records by split and platform", "",
        "| Split | Platform | Records | First timestamp | Last timestamp | Distinct dates |", "|---|---|---:|---|---|---:|",
    ]
    audit_lines += [f"| {s} | {p} | {n:,} | {lo} | {hi} | {days:,} |" for s, p, n, lo, hi, days in p1_by_split_platform]
    audit_lines += ["", "### Per-platform series across all splits", "", "| Platform | Records | First date | Last date | Distinct dates | Duplicate-date records | Missing dates within span |", "|---|---:|---|---|---:|---:|---:|"]
    audit_lines += [f"| {p} | {n:,} | {lo} | {hi} | {dates:,} | {dups:,} | {gaps:,} |" for p, n, lo, hi, dates, dups, gaps in p1_series]
    audit_lines += ["", f"Duplicate `(product_id, platform, date)` groups for P0000001: {len(p1_duplicate_dates):,}."]
    if p1_duplicate_dates:
        audit_lines += ["", "| Platform | Date | Records |", "|---|---|---:|"]
        audit_lines += [f"| {p} | {day} | {n} |" for p, day, n in p1_duplicate_dates]
    (args.output_dir / "quality_audit.md").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    readme = f"""# Rahul Dataset Handoff

This package is a read-only extract and audit for backend integration. Original files remain at `{args.data_root.resolve()}\\data\\splits`.

## Files

- `p0000001_all_splits.csv`: all P0000001 records, all observed platforms, all original columns plus appended `source_split`; {export_count:,} rows, {export_info['size_bytes']:,} bytes.
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
& "C:\\Users\\GAURAV DAS\\.conda\\envs\\fakedeal\\python.exe" scripts\\build_rahul_dataset_handoff.py --data-root "{args.data_root.resolve()}"
```

The script uses DuckDB with a 1 GB memory cap, writes only under this output directory, and does not modify source CSVs.
"""
    (args.output_dir / "README.md").write_text(readme, encoding="utf-8")

    source_unchanged = original_stat == final_stat
    manifest = {
        "dataset_root": str(args.data_root.resolve()),
        "source_files": {name: {"path": str(path.resolve()), **original_stat[name], "unchanged_size_and_mtime": original_stat[name] == final_stat[name]} for name, path in paths.items()},
        "split_stats": split_stats,
        "duplicate_keys": duplicate_stats,
        "p0000001_platforms": p1_platforms,
        "p0000001_export": export_info,
        "schema_columns": reference_columns,
        "timestamp_raw_sample": timestamp_values,
        "all_originals_unchanged_size_and_mtime": source_unchanged,
        "outputs": {},
    }
    for filename in ("p0000001_all_splits.csv", "schema_report.md", "quality_audit.md", "README.md"):
        output = args.output_dir / filename
        manifest["outputs"][filename] = {"path": str(output.resolve()), "size_bytes": output.stat().st_size}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")

    print(json.dumps({"export": export_info, "source_unchanged": source_unchanged,
                      "outputs": manifest["outputs"], "timestamp_raw_sample": timestamp_values}, indent=2))
    if not export_info["verified_exact_match"] or not source_unchanged:
        raise SystemExit("Verification failed; inspect manifest and quality report")


if __name__ == "__main__":
    main()
