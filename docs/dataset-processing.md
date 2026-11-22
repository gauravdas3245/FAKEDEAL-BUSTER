# Original dataset audit and runtime store

## Source lineage and path

The requested `C:\end sem project\dataset` path is not present in this workspace. The repository handoff lineage manifest instead names `C:\end sem project\archive (5)`, whose extracted metadata and source splits match the existing project lineage. This task used only that extracted original Kaggle dataset and did not modify it. Re-run the builder with the folder containing `data/splits` via `--data-root` or `FAKEDEAL_RAW_DATA_DIR`.

The source identifies itself as the E-Commerce Product Price Tracker Dataset, version 1.0.0. Its metadata reports 25,606,940 rows and 46 columns. The chronological source splits are `ecommerce_train.csv` (20,450,474 rows), `ecommerce_val.csv` (2,560,694), and `ecommerce_test.csv` (2,595,772). They cover 2023-01-01 to 2024-12-30. Processing reads the three mutually exclusive split files only; it does not concatenate the separate full or forecast exports.

The dataset contains 9,980 product IDs and 35,078 observed product/platform combinations across Amazon, Best Buy, eBay, Flipkart, and Walmart; categories are Appliances, Books, Electronics, Fashion, Gaming, Household, and Sports. Identity metadata includes title, brand, category, subcategory, platform, and ASIN. It contains timestamped price, original price, discount percentage, product-level average rating, review count, inventory/state fields, engineered historical fields, and labels/targets. It has no product URL, seller name, or seller rating. `avg_rating` describes a product and is not a seller rating. The full derived store contains no conflicting ASIN values within a product/platform identity; the Amazon ASIN lookup uses that exact verified identity relation.

## Derived store

`scripts/build_runtime_store.py` reads the source in DuckDB CSV streaming queries and creates `artifacts/derived/fakedeal_runtime.duckdb` separately. The resulting read-only runtime store is approximately 2.09 GB and has indexed `observations`, `products`, and `product_platforms` tables. It includes only identity/price metadata needed by the application and does not feed source target fields into live inference. It records lineage, source file sizes, row count, unique counts, date range, and metadata availability flags in `store_metadata`.

Build once (destination must not already exist; the script refuses to overwrite):

```powershell
& 'C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe' scripts/build_runtime_store.py --data-root 'C:\end sem project\archive (5)'
```

For another machine, point `--data-root` to the read-only extracted original dataset directory. Do not copy the compact P1 integration extract in place of the original splits. The DuckDB store is local derived data and should not be committed; the builder is reproducible from the original dataset.

## Identity and history semantics

Catalogue matching uses exact product title after case/spacing/punctuation normalization and requires a matching actual category and platform. Duplicate identity matches return ambiguity candidates; no nearest-title substitution occurs. Amazon URL matching parses only recognized Amazon product paths and checks the exact extracted ASIN against the matching dataset row and submitted metadata. Other URL domains are not treated as identity evidence.

The backend requests historical rows strictly before the selected timestamp. It deduplicates identical same-date values and returns `HISTORY_CONFLICT` for differing valid prices on the same key/date. It does not fabricate dates, forward-fill, or interpolate. The ML service retains its canonical four features and minimum-history checks. Since the data ends in 2024, current analysis in 2026 has no current-period price history and returns `NEEDS_MORE_DATA`.

## Limitations

The dataset is a synthetic project dataset rather than verified live marketplace transactions. The source includes `fake_discount_flag`, `price_spike_flag`, and future targets `target_price_7d`, `target_price_30d`, and `target_price_direction_7d`; their existence alone does not validate a fraud label or justify using future targets as live inputs. The dataset's 25.6M chronological observations and explicit future price targets provide enough raw material for a separate forecast experiment, but this repository has no forecast model or temporal baseline/error evaluation. No forecast is exposed until that evaluation exists. Central FDI live inference remains `INSUFFICIENT_INPUTS` when required independent signals are absent. Seller reputation analysis is unsupported because seller identity and seller rating fields are absent.
