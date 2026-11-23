# Fake Discount Index (FDI): provisional methodology

**Status: PROVISIONAL / NOT VALIDATED.** The weights, component transforms, and interpretation bands below are hypotheses for review. They have not been calibrated against verified fake-discount labels, scientifically validated, or mentor-approved. The dataset's `fake_discount_flag` has no positive examples, so this work does not claim fraud classification performance.

FDI is a separate heuristic pricing index. It is not part of the Isolation Forest's four-feature vector, is not a fraud probability or confidence score, and does not establish that a discount is fake. No combined model/FDI verdict is defined.

## Proposed formulas

All component scores are clipped to `[0, 100]`:

| Component | Proposed calculation | Weight |
|---|---|---:|
| `S_gap` | `clip((discount_pct - real_discount_30d) / 50, 0, 1) * 100` | 0.35 |
| `S_mean_ratio` | `clip((ratio_to_30d_avg - 0.85) / 0.30, 0, 1) * 100` | 0.30 |
| `S_msrp_inflation` | `clip((msrp_inflation_ratio - 1) / 0.25, 0, 1) * 100` | 0.20 |
| `S_anomaly` | `clip(0.6 * (price_spike_flag * 100) + 0.4 * (pre_discount_hike_ratio / 0.20 * 100), 0, 100)` | 0.15 |

If every required input is available and valid:

`FDI = 0.35*S_gap + 0.30*S_mean_ratio + 0.20*S_msrp_inflation + 0.15*S_anomaly`

The weights sum to 1.0. Proposed bands are `0–29 LOW`, `30–59 MODERATE`, `60–79 HIGH`, and `80–100 CRITICAL`. Numeric boundaries map continuously: `[0,30)`, `[30,60)`, `[60,80)`, and `[80,100]`. These bands are provisional and are not validated decision thresholds.

## Input audit and inference availability

| Signal | Audit finding | Inference availability |
|---|---|---|
| `discount_pct` | The feature audit documents `(original_price - price) / original_price * 100`; it is also present in the source schema. | Recomputable from the submitted positive current and original prices. The inference adapter derives it; it does not trust/copy a dataset value. |
| `real_discount_30d` | Existing feature extraction defines it as `(prior_30d_mean_price - current_price) / prior_30d_mean_price * 100`. | Recomputed from inference's `ratio_to_30d_avg`: `(1 - ratio_to_30d_avg) * 100`. This uses strictly prior history from the inference engine. |
| `ratio_to_30d_avg` | Verified model feature: `current_price / prior_30d_mean_price`. | Available only when historical inference returns `status="OK"`. |
| `msrp_inflation_ratio` | The verified `msrp_to_30d_avg` feature is `original_price / prior_30d_mean_price`. | Available only when historical inference returns `status="OK"`; the adapter maps this feature without alteration. |
| `price_spike_flag` | A source dataset label with 48,554 positive values. The audit says its generation rule/code is unavailable; it reflects price-spike anomalies and is not fake-discount ground truth. | **Not independently computable under the documented inference contract.** Do not copy the historical dataset flag into live inference. |
| `pre_discount_hike_ratio` | Not one of the audited 46 schema columns; no verified formula or source definition was found. | **Unavailable.** No formula is invented here. |

Therefore, current inference can calculate `S_gap`, `S_mean_ratio`, and `S_msrp_inflation` when it has sufficient history. It cannot reliably calculate `S_anomaly`, because both required inputs are unavailable at inference time. The official total remains null with `status="INSUFFICIENT_INPUTS"`; the implementation does not drop the component or renormalize weights. For cold-start inference, the historical-dependent component scores are also null and their required signals are listed as missing.

The general pure `calculate_fdi(inputs)` function can evaluate the proposed arithmetic when a caller supplies all six inputs. Such values must be independently and legitimately sourced; supplying a dataset label does not make the result operationally valid. The inference adapter `calculate_fdi_from_inference(...)` deliberately does not derive either unavailable anomaly input and does not substitute the Isolation Forest anomaly score.

## Validation and output contract

`ml.fdi.calculate_fdi` returns:

- `status`: `OK` only when all inputs exist and validate; otherwise `INSUFFICIENT_INPUTS`.
- `fdi_score` and `provisional_level`: null if any required signal is missing.
- `component_scores`: available diagnostic components, with unavailable components as null.
- `component_weights`: the unchanged proposed weights.
- `missing_inputs`: exact unavailable signal names.
- `explanation`, `methodology_version="fdi_provisional_v1"`, and `validation_status="PROVISIONAL_NOT_VALIDATED"`.

Malformed, negative where semantically invalid, non-finite, or out-of-range values raise `ValueError`. A negative `real_discount_30d` is permitted because it describes a current price above its prior mean; its formula is not clipped, while the component output is clipped.

## Backend-neutral integration example

Initialize/reuse the existing inference engine as documented in `ml-inference-guide.md`. Once a historical prediction returns `OK`, pass it to the adapter:

```python
from ml.fdi import calculate_fdi_from_inference

fdi = calculate_fdi_from_inference(
    inference_result,
    current_price=request.current_price,
    original_price=request.original_price,
)
# Current expected status: INSUFFICIENT_INPUTS because the two anomaly inputs
# have no verified inference-time derivation. Do not invent or copy them.
```

Keep response sections distinct:

- **ML anomaly result:** the saved Isolation Forest flag and anomaly score.
- **FDI heuristic result:** provisional component diagnostics; total unavailable until every input has a validated source.
- **`NEEDS_MORE_DATA`:** historical inference could not calculate its feature vector.
- **`INSUFFICIENT_INPUTS`:** FDI-specific signals are unavailable even if ML inference succeeded.

No API route, combined verdict, risk threshold, or confidence field is prescribed. The inference engine and FDI module remain independent of FastAPI.

## Demo

Run `python scripts/demo_fdi.py` in the verified Conda environment. Both the complete-formula example and the live-adapter example are clearly labelled synthetic illustrations. They are not real product evidence, model evaluation, or fraud detection performance.
