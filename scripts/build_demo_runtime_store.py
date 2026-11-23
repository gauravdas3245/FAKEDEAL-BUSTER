"""
Build a lightweight demonstration DuckDB store for free cloud deployments (Render / Vercel).
Extracts a deterministic subset of products and observations from the full runtime store
while preserving 100% schema fidelity and indexed query capabilities.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FULL_DB = ROOT / "artifacts" / "derived" / "fakedeal_runtime.duckdb"
DEFAULT_DEMO_DB = ROOT / "artifacts" / "derived" / "fakedeal_demo.duckdb"


def build_demo_store(full_path: Path, demo_path: Path, product_limit: int = 105) -> dict:
    if not full_path.is_file():
        raise FileNotFoundError(f"Source runtime store not found: {full_path}")

    demo_path.parent.mkdir(parents=True, exist_ok=True)
    if demo_path.exists():
        demo_path.unlink()

    full_sql_path = "'" + full_path.resolve().as_posix().replace("'", "''") + "'"
    per_cat = max(1, product_limit // 7)
    
    con = duckdb.connect(str(demo_path))
    try:
        con.execute(f"ATTACH {full_sql_path} AS full_store (READ_ONLY)")
        
        # 1. Stratified Products across all categories
        con.execute(f"""
            CREATE TABLE products AS
            WITH ranked AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY product_id) as rn
                FROM full_store.products
            )
            SELECT * EXCLUDE (rn)
            FROM ranked
            WHERE rn <= {per_cat}
            ORDER BY product_id
        """)
        prod_count = con.execute("SELECT count(*) FROM products").fetchone()[0]
        
        # 2. Product Platforms
        con.execute("""
            CREATE TABLE product_platforms AS
            SELECT pp.* FROM full_store.product_platforms pp
            JOIN products p ON pp.product_id = p.product_id
        """)
        pp_count = con.execute("SELECT count(*) FROM product_platforms").fetchone()[0]
        
        # 3. Observations
        con.execute("""
            CREATE TABLE observations AS
            SELECT o.* FROM full_store.observations o
            JOIN products p ON o.product_id = p.product_id
        """)
        obs_count = con.execute("SELECT count(*) FROM observations").fetchone()[0]
        
        # 4. Metadata
        con.execute("""
            CREATE TABLE store_metadata AS
            SELECT * FROM full_store.store_metadata
        """)
        
        # Update metadata to reflect demonstration store
        con.execute(f"DELETE FROM store_metadata WHERE key in ('source_type', 'demo_subset_products')")
        con.execute(f"INSERT INTO store_metadata VALUES ('source_type', 'Demonstration Seed Store ({product_limit} Products)')")
        con.execute(f"INSERT INTO store_metadata VALUES ('demo_subset_products', '{product_limit}')")
        
        # 5. Indexes
        con.execute("CREATE INDEX observations_lookup_idx ON observations(product_id, platform, timestamp)")
        con.execute("CREATE INDEX products_name_idx ON products(title)")
        con.execute("CREATE INDEX product_platform_lookup_idx ON product_platforms(product_id, platform)")
        
        con.execute("DETACH full_store")
    finally:
        con.close()

    size_bytes = demo_path.stat().st_size
    return {
        "output_path": str(demo_path),
        "products": prod_count,
        "product_platforms": pp_count,
        "observations": obs_count,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2)
    }


def main():
    parser = argparse.ArgumentParser(description="Build lightweight demo DuckDB store")
    parser.add_argument("--source", type=Path, default=DEFAULT_FULL_DB, help="Full DuckDB store path")
    parser.add_argument("--output", type=Path, default=DEFAULT_DEMO_DB, help="Demo DuckDB store path")
    parser.add_argument("--limit", type=int, default=100, help="Number of products to include")
    args = parser.parse_args()

    print(f"Building demo DuckDB from {args.source} to {args.output} (Limit: {args.limit} products)...")
    res = build_demo_store(args.source, args.output, args.limit)
    print("Demo DuckDB created successfully:")
    for k, v in res.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
