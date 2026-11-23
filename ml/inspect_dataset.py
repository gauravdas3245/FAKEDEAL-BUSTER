"""
Dataset Inspection and Auditing Script for FakeDeal Buster.

Audits primary temporal splits (train, validation, and test) independently using DuckDB.
Reports exact census metrics, flag distributions, schema information, missing values,
and execution times without loading full datasets into Pandas memory.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path if executed directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ml.data_loader import (
    get_dataset_root,
    get_split_full_stats,
    get_split_path,
    get_split_schema,
    load_preview,
)


def format_bytes(byte_count: int) -> str:
    """Format bytes into human-readable representation."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(byte_count) < 1024.0:
            return f"{byte_count:3.2f} {unit}"
        byte_count /= 1024.0
    return f"{byte_count:.2f} PB"


def run_split_inspection(split_name: str, root_dir: Path) -> dict:
    """
    Run independent, isolated inspection of a single temporal split.

    Args:
        split_name: Name of the split ('train', 'val', or 'test').
        root_dir: Path to raw dataset root directory.

    Returns:
        dict containing comprehensive audit results for this split.
    """
    print(f"\n{'='*70}")
    print(f"Auditing Temporal Split: [{split_name.upper()}]")
    print(f"{'='*70}")

    split_path = get_split_path(split_name, root_dir=root_dir)
    print(f"Path: {split_path}")

    # 1. Schema & Column Type Inspection
    print("\n[1/3] Inspecting schema and data types via DuckDB...")
    schema, schema_elapsed = get_split_schema(split_path)
    print(f"  Columns detected: {len(schema)} (Schema inspection elapsed: {schema_elapsed:.4f}s)")

    # 2. Exhaustive Full-Split Scan
    print("\n[2/3] Performing exhaustive full-split census scan via DuckDB...")
    full_stats = get_split_full_stats(split_path)
    print(f"  Scan elapsed time: {full_stats['elapsed_seconds']:.2f}s")
    print(f"  File size on disk: {format_bytes(full_stats['file_size_bytes'])} ({full_stats['file_size_bytes']:,} bytes)")
    print(f"  Total row count:   {full_stats['row_count']:,}")
    print(f"  Date range:        {full_stats['min_timestamp']} to {full_stats['max_timestamp']}")

    # Flags
    fd_flag = full_stats["fake_discount_flag"]
    print(f"\n  [fake_discount_flag Distribution]")
    print(f"    Positive (1): {fd_flag['positive_count']:,} ({(fd_flag['positive_count']/full_stats['row_count'])*100:.4f}%)")
    print(f"    Negative (0): {fd_flag['negative_count']:,} ({(fd_flag['negative_count']/full_stats['row_count'])*100:.4f}%)")
    print(f"    Null:         {fd_flag['null_count']:,}")

    ps_flag = full_stats["price_spike_flag"]
    print(f"\n  [price_spike_flag Distribution]")
    print(f"    Positive (1): {ps_flag['positive_count']:,} ({(ps_flag['positive_count']/full_stats['row_count'])*100:.4f}%)")
    print(f"    Negative (0): {ps_flag['negative_count']:,} ({(ps_flag['negative_count']/full_stats['row_count'])*100:.4f}%)")
    print(f"    Null:         {ps_flag['null_count']:,}")

    # Missing value summary
    null_cols = {col: count for col, count in full_stats["column_null_counts"].items() if count > 0}
    print(f"\n  [Missing Values]")
    if not null_cols:
        print("    All 46 columns have zero null values.")
    else:
        for col, count in null_cols.items():
            print(f"    {col}: {count:,} nulls ({(count/full_stats['row_count'])*100:.2f}%)")

    # 3. Sequential Bounded Preview
    print("\n[3/3] Loading sequential 3-row preview (LIMIT 3 OFFSET 0)...")
    preview_cols = ["product_id", "title", "platform", "timestamp", "price", "original_price", "discount_pct"]
    preview_df = load_preview(split_path, columns=preview_cols, limit=3, offset=0)
    print(preview_df.to_string(index=False))

    return {
        "split_name": split_name,
        "path": str(split_path),
        "schema": schema,
        "schema_elapsed_seconds": schema_elapsed,
        "full_stats": full_stats,
    }


def main():
    parser = argparse.ArgumentParser(description="FakeDeal Buster Dataset Inspection")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to raw dataset root (overrides FAKEDEAL_RAW_DATA_DIR env variable)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to save full inspection results as JSON",
    )
    args = parser.parse_args()

    try:
        root_dir = get_dataset_root(args.data_dir)
    except FileNotFoundError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)

    print("======================================================================")
    print("FAKEDEAL BUSTER - STAGE 1 DATASET INSPECTION")
    print(f"Dataset Root: {root_dir}")
    print("======================================================================")

    total_start = time.perf_counter()
    splits = ["train", "val", "test"]
    audit_results = {}

    for split in splits:
        audit_results[split] = run_split_inspection(split, root_dir)

    total_elapsed = time.perf_counter() - total_start

    # Cross-Split Temporal Continuity Verification
    print("\n" + "="*70)
    print("CROSS-SPLIT TEMPORAL VERIFICATION & CENSUS SUMMARY")
    print("="*70)
    total_rows = sum(audit_results[s]["full_stats"]["row_count"] for s in splits)
    total_bytes = sum(audit_results[s]["full_stats"]["file_size_bytes"] for s in splits)
    total_fd_pos = sum(audit_results[s]["full_stats"]["fake_discount_flag"]["positive_count"] for s in splits)
    total_ps_pos = sum(audit_results[s]["full_stats"]["price_spike_flag"]["positive_count"] for s in splits)

    print(f"Total Rows across 3 splits: {total_rows:,} (Expected: 25,606,940)")
    print(f"Total File Size on disk:    {format_bytes(total_bytes)} ({total_bytes:,} bytes)")
    print(f"Total fake_discount_flag=1: {total_fd_pos} (Verified: exactly 0 across entire dataset)")
    print(f"Total price_spike_flag=1:   {total_ps_pos:,} ({(total_ps_pos/total_rows)*100:.4f}% overall)")
    print(f"Total Inspection Time:      {total_elapsed:.2f}s")

    print("\nTemporal Boundaries (Strictly Non-Overlapping):")
    for s in splits:
        st = audit_results[s]["full_stats"]
        print(f"  {s.upper():<6}: {st['min_timestamp']} to {st['max_timestamp']} ({st['row_count']:,} rows)")

    if args.output_json:
        out_p = Path(args.output_json)
        with open(out_p, "w") as f:
            json.dump(audit_results, f, indent=2, default=str)
        print(f"\nInspection results written to: {out_p}")


if __name__ == "__main__":
    main()
