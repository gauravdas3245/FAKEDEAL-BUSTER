"""Reproducible synthetic artificial-discount experiment.

Labels describe generated scenarios only. They are not observations or
ground-truth claims about actual marketplaces, sellers, or fraud.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd


SYNTHETIC_VERSION = "synthetic_discount_scenarios_v1"
SEED = 20261118
NUMERIC_FEATURES = (
    "msrp_to_30d_avg",
    "ratio_to_30d_avg",
    "price_volatility_30d",
    "recent_7d_surge",
    "advertised_discount_pct",
)
CATEGORICAL_FEATURES = ("platform", "category")
FEATURE_NAMES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "scenario_label"
LABELS = {0: "SYNTHETIC_GENUINE_DISCOUNT", 1: "SYNTHETIC_ARTIFICIALLY_INFLATED_DISCOUNT"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sample_reference_profiles(source_csv: Path, sample_size: int = 60000, seed: int = SEED) -> pd.DataFrame:
    """Read a bounded reproducible sample of valid rows from an original split.

    No product IDs, target columns, or future targets are selected.
    """
    if sample_size < 100:
        raise ValueError("sample_size must be at least 100")
    if not source_csv.is_file():
        raise FileNotFoundError(f"Original source split not found: {source_csv}")
    csv_path = source_csv.resolve().as_posix().replace("'", "''")
    query = f"""
        SELECT platform, category,
               original_price / price_30d_avg AS msrp_to_30d_avg,
               price / price_30d_avg AS ratio_to_30d_avg,
               price_30d_std / price_30d_avg AS price_volatility_30d,
               greatest(0.0, (price_7d_max - price_30d_avg) / price_30d_avg) AS recent_7d_surge,
               greatest(0.0, least(100.0, (original_price - price) / original_price * 100.0)) AS advertised_discount_pct
        FROM (
            SELECT platform, category, price, original_price, price_30d_avg,
                   price_30d_std, price_7d_max
            FROM read_csv_auto('{csv_path}', header=true)
            WHERE platform IS NOT NULL AND category IS NOT NULL
              AND isfinite(price) AND price > 0
              AND isfinite(original_price) AND original_price >= price
              AND isfinite(price_30d_avg) AND price_30d_avg > 0
              AND isfinite(price_30d_std) AND price_30d_std >= 0
              AND isfinite(price_7d_max) AND price_7d_max > 0
        ) AS valid_profiles
        USING SAMPLE reservoir({int(sample_size)} ROWS) REPEATABLE ({int(seed)})
        LIMIT {int(sample_size)}
    """
    try:
        with duckdb.connect() as connection:
            profiles = connection.execute(query).fetchdf()
    except duckdb.Error as exc:
        raise RuntimeError("Could not read a bounded reference sample from the original training split") from exc
    profiles = profiles.replace([np.inf, -np.inf], np.nan).dropna()
    if len(profiles) < 100:
        raise ValueError("Fewer than 100 valid reference profiles were sampled")
    return profiles.reset_index(drop=True)


def generate_synthetic_scenarios(
    profiles: pd.DataFrame,
    row_count: int = 40000,
    seed: int = SEED,
) -> pd.DataFrame:
    """Generate balanced scenario labels from observed profile ranges.

    The scenario is assigned as a latent generator condition. The target column
    is not used in, or included among, model features. Genuine cases use
    empirical below-average sale ratios and observed discount magnitudes;
    artificial cases retain near-baseline current prices while synthetically
    inflating the advertised reference price using observed markup ranges.
    """
    required = {"platform", "category", *NUMERIC_FEATURES}
    missing = required.difference(profiles.columns)
    if missing:
        raise ValueError(f"Reference sample lacks columns: {sorted(missing)}")
    if row_count < 300:
        raise ValueError("row_count must be at least 300")
    rng = np.random.default_rng(seed)
    clean = profiles.copy().replace([np.inf, -np.inf], np.nan).dropna(subset=list(required))
    clean = clean[(clean["msrp_to_30d_avg"] > 0) & (clean["ratio_to_30d_avg"] > 0)
                  & (clean["price_volatility_30d"] >= 0) & (clean["recent_7d_surge"] >= 0)]
    if len(clean) < max(100, row_count):
        raise ValueError("Need at least one unique valid source profile per generated scenario row")

    ratio_values = clean["ratio_to_30d_avg"].to_numpy(dtype=float)
    good_ratios = ratio_values[(ratio_values > 0.2) & (ratio_values < 1.0)]
    near_baseline = ratio_values[(ratio_values >= 0.85) & (ratio_values <= 1.2)]
    discounts = clean["advertised_discount_pct"].to_numpy(dtype=float)
    discounts = discounts[(discounts >= 3.0) & (discounts <= 75.0)]
    observed_markups = clean["msrp_to_30d_avg"].to_numpy(dtype=float)
    observed_markups = observed_markups[(observed_markups >= 0.7) & (observed_markups <= 4.0)]
    if min(len(good_ratios), len(near_baseline), len(discounts), len(observed_markups)) < 25:
        raise ValueError("Observed data lacks sufficient valid price patterns for scenario generation")

    quantile_90 = float(np.quantile(observed_markups, 0.90))
    quantile_99 = float(np.quantile(observed_markups, 0.99))
    max_inflated_msrp = max(2.0, quantile_99 * 1.5)
    class_labels = np.tile(np.array([0, 1], dtype=np.int8), (row_count + 1) // 2)[:row_count]
    rng.shuffle(class_labels)
    chosen_indices = rng.choice(len(clean), size=row_count, replace=False)
    chosen = clean.iloc[chosen_indices].reset_index(drop=True)

    current_ratio = np.empty(row_count, dtype=float)
    msrp_ratio = np.empty(row_count, dtype=float)
    for index, label in enumerate(class_labels):
        if label == 0:
            current = float(rng.choice(good_ratios))
            claimed = float(rng.choice(discounts))
            listed = current / max(1e-6, 1.0 - claimed / 100.0)
            current_ratio[index] = current
            msrp_ratio[index] = listed
        else:
            current = float(rng.choice(near_baseline))
            empirical_msrp = float(rng.choice(observed_markups))
            inflation_factor = float(rng.uniform(1.10, 1.55))
            listed = max(empirical_msrp * inflation_factor, current * float(rng.uniform(1.25, 1.9)))
            current_ratio[index] = current
            msrp_ratio[index] = min(listed, max_inflated_msrp)
            if msrp_ratio[index] <= current:
                msrp_ratio[index] = current * 1.25

    result = pd.DataFrame({
        "msrp_to_30d_avg": msrp_ratio,
        "ratio_to_30d_avg": current_ratio,
        "price_volatility_30d": chosen["price_volatility_30d"].to_numpy(dtype=float),
        "recent_7d_surge": chosen["recent_7d_surge"].to_numpy(dtype=float),
        "advertised_discount_pct": np.clip((1.0 - current_ratio / msrp_ratio) * 100.0, 0.0, 95.0),
        "platform": chosen["platform"].astype(str).str.casefold().to_numpy(),
        "category": chosen["category"].astype(str).to_numpy(),
        TARGET_COLUMN: class_labels,
        "scenario_name": [LABELS[int(label)] for label in class_labels],
    })
    result = result.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    if result[TARGET_COLUMN].nunique() != 2:
        raise ValueError("Generated scenarios must contain both classes")
    return result


def split_synthetic_scenarios(
    scenarios: pd.DataFrame,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create stratified independent synthetic-example train/validation/test sets.

    These are generated IID offers, not time-series records; a stratified split
    is therefore appropriate. The split seed is fixed and recorded.
    """
    from sklearn.model_selection import train_test_split

    train, remainder = train_test_split(scenarios, test_size=0.30, random_state=seed,
                                        stratify=scenarios[TARGET_COLUMN])
    validation, test = train_test_split(remainder, test_size=0.50, random_state=seed + 1,
                                        stratify=remainder[TARGET_COLUMN])
    return tuple(frame.reset_index(drop=True) for frame in (train, validation, test))


def write_dataset_bundle(
    profiles: pd.DataFrame,
    output_dir: Path,
    row_count: int = 40000,
    seed: int = SEED,
    source_file: str = "C:/end sem project/archive (5)/data/splits/ecommerce_train.csv",
    overwrite: bool = False,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing synthetic dataset files: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = generate_synthetic_scenarios(profiles, row_count=row_count, seed=seed)
    splits = split_synthetic_scenarios(generated, seed=seed)
    file_info = {}
    for filename, frame in zip(("train.csv", "validation.csv", "test.csv"), splits):
        path = output_dir / filename
        frame.to_csv(path, index=False, float_format="%.10g")
        file_info[filename] = {"rows": len(frame), "sha256": sha256_file(path),
                               "class_counts": {str(k): int(v) for k, v in frame[TARGET_COLUMN].value_counts().sort_index().items()}}
    manifest = {
        "dataset_version": SYNTHETIC_VERSION,
        "synthetic_only": True,
        "real_world_fraud_labels": False,
        "label_definition": {
            "0": LABELS[0] + ": current price is generated from observed below-average ratios with an observed discount magnitude.",
            "1": LABELS[1] + ": current price remains near its observed historical baseline while advertised reference price is inflated by a documented generator factor.",
            "not_ground_truth": "Labels denote assigned generator scenarios only; they are not verified fraud or claims about real listings.",
        },
        "source": {"original_train_split": source_file, "reference_profile_rows": len(profiles),
                   "sampling": "DuckDB reservoir sample of the original chronological training split; valid observed price/rolling feature fields only; no IDs or target/future-label columns selected.",
                   "sampled_numeric_ranges": {
                       column: {"min": float(profiles[column].min()),
                                "p05": float(profiles[column].quantile(0.05)),
                                "median": float(profiles[column].median()),
                                "p95": float(profiles[column].quantile(0.95)),
                                "max": float(profiles[column].max())}
                       for column in NUMERIC_FEATURES
                   },
                   "platforms": sorted(profiles["platform"].astype(str).str.casefold().unique().tolist()),
                   "categories": sorted(profiles["category"].astype(str).unique().tolist())},
        "generation": {"row_count": len(generated), "seed": seed, "class_balance": "balanced by generator design",
                       "source_profile_reuse": "none; each synthetic row receives a distinct sampled source profile before split assignment",
                       "generator_version": SYNTHETIC_VERSION,
                       "feature_names": list(FEATURE_NAMES),
                       "target_column": TARGET_COLUMN,
                       "split_method": "stratified random split over independent IID generated offers; 70/15/15"},
        "splits": file_info,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
