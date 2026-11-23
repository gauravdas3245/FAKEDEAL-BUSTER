"""Build a separate reproducible synthetic discount-scenario dataset."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.synthetic_discount import SEED, sample_reference_profiles, write_dataset_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT.parent / "archive (5)" / "data" / "splits" / "ecommerce_train.csv",
                        help="Original chronological training split used only for feature-range sampling")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/synthetic/discount_scenarios_v1")
    parser.add_argument("--rows", type=int, default=40000)
    parser.add_argument("--sample-size", type=int, default=60000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--overwrite", action="store_true", help="Overwrite only this synthetic output directory")
    args = parser.parse_args()
    profiles = sample_reference_profiles(args.source, args.sample_size, args.seed)
    manifest = write_dataset_bundle(profiles, args.output, args.rows, args.seed,
                                    source_file=str(args.source), overwrite=args.overwrite)
    print(f"Synthetic dataset created at {args.output}")
    print(f"Reference rows sampled: {len(profiles)}")
    print(f"Synthetic split rows: {manifest['generation']['row_count']}")
    print(f"Split counts: { {name: value['rows'] for name, value in manifest['splits'].items()} }")
    print("Labels are generated scenarios, not real-world fraud ground truth.")


if __name__ == "__main__":
    main()
