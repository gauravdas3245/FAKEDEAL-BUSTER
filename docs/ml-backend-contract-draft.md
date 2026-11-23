# Provisional ML-to-Backend Interface Contract

**Document Status:** **PROVISIONAL (DRAFT)**  
**Target Reviewer:** Rahul Amin (Backend Developer)  
**Author:** Gaurav Das (Team Leader & ML Developer)  
**Date:** 16 November 2026 (Drafted 17 November 2026 early hours)  
**Notice:** *This specification is a provisional design contract for team discussion. It has NOT yet been accepted or confirmed by Rahul Amin and is subject to backend review and mutual agreement.*

---

## 1. Endpoint Route Discrepancy & Action Required

> [!WARNING]
> **Endpoint Naming Discrepancy:**
> - [docs/api-documentation.md](file:///C:/end%20sem%20project/FAKEDEAL-BUSTER/docs/api-documentation.md) and [backend/README.md](file:///C:/end%20sem%20project/FAKEDEAL-BUSTER/backend/README.md) define the endpoint as: `POST /api/analyze`
> - [FakeDeal_Buster_Group_B_Final_PRD.docx](file:///C:/end%20sem%20project/FakeDeal_Buster_Group_B_Final_PRD.docx) (Section 6) refers to the endpoint as: `POST /analyze`
> 
> **Pending Decision:** This discrepancy is deliberately preserved and **not** silently chosen. **Rahul Amin must formally confirm** whether the FastAPI backend router will mount routes under `/api` (`/api/analyze`) or at root (`/analyze`).

---

## 2. Structural Field Taxonomy

To prevent data leakage, operational failures, and confusion between user inputs, computed historical metrics, and model outputs, fields are strictly segregated into four categories:

### A. User-Provided Input Fields (Frontend &rarr; Backend)
Fields directly submitted by the user through the React product inspector form:

| Field Name | Type | Required? | Validation Rules & Constraints | Description |
|---|---|---|---|---|
| `product_name` | `string` | **Required** | `min_length=1`, `max_length=255`, trimmed whitespace | The name or title of the product listing |
| `current_price` | `float` | **Required** | `gt=0.0`, reasonable upper bound (e.g., `<= 1000000.0`) | Advertised selling price in local currency / USD |
| `original_price` | `float` | **Required** | `gt=0.0`, must satisfy `original_price >= current_price` for standard discount | Advertised reference or "strikethrough" price |
| `platform` | `string` | Optional | Allowed: `["amazon", "flipkart", "ebay", "walmart", "bestbuy", "other"]` (default: `"amazon"`) | Marketplace hosting the deal |
| `category` | `string` | Optional | Allowed: `["Electronics", "Fashion", "Gaming", "Appliances", "Books", "Household", "Sports", "Other"]` | Product category |
| `product_url` | `string` | Optional | Optional valid URL format or empty string. *Must not trigger server-side scraping in MVP.* | Reference listing URL |
| `historical_prices` | `list[HistoricalPricePoint]` | Optional | Default: `[]`. Array of historical daily observations | Optional list of known previous prices |

**HistoricalPricePoint Schema:**
```json
{
  "date": "YYYY-MM-DD",
  "price": 149.99
}
```

---

### B. Historical & Dataset-Derived Features (Internal Backend/ML Processing)
Features computed internally when `historical_prices` are supplied or resolved against catalog caches:

| Feature Name | Type | Availability Condition | Computation Logic |
|---|---|---|---|
| `discount_pct` | `float` | Always Computable | `((original_price - current_price) / original_price) * 100.0` |
| `history_count` | `int` | Always Computable | Length of `historical_prices` array |
| `price_30d_median` | `float` or `null` | Requires $\ge 7$ historical records | Median of observations within trailing 30-day window |
| `price_30d_min` | `float` or `null` | Requires $\ge 7$ historical records | Minimum observed selling price in trailing 30 days |
| `pre_sale_markup_pct`| `float` or `null` | Requires valid `price_30d_median` | `((original_price - price_30d_median) / price_30d_median) * 100.0` |
| `is_at_all_time_low` | `bool` or `null` | Requires $\ge 30$ historical records | `current_price <= min(historical_prices)` |

> [!NOTE]
> If `history_count < 7`, all trailing rolling features evaluate to `null`. The system gracefully downgrades to cold-start evaluation.

---

### C. Model & Scoring Output Fields (Backend &rarr; Frontend)
The analysis payload returned to the React frontend:

| Output Field | Type | Nullable? | Permitted Values / Constraints | Description |
|---|---|---|---|---|
| `product_name` | `string` | No | Matches input | Echoed product name |
| `current_price` | `float` | No | Matches input | Echoed current price |
| `original_price` | `float` | No | Matches input | Echoed original price |
| `discount_percentage` | `float` | No | Rounded to 1 decimal place | Calculated discount percentage |
| `verdict` | `string` | No | **Strict Enum (4 States Only):**<br>1. `"Potential Fake Discount"`<br>2. `"Suspicious Pricing"`<br>3. `"No Strong Fake-Discount Signal"`<br>4. `"Needs More Data"` | Standardized deal assessment verdict.<br>*(Note: `"Genuine Deal"` is strictly prohibited)* |
| `confidence_score` | `float` | **Yes (`null`)** | `0.0` to `1.0` if calibrated probability exists; **`null` for heuristic FDI** | Must NOT represent uncalibrated heuristic scores as probabilities |
| `fdi_score` | `float` | No | `0.0` to `100.0` | Fake Discount Index (heuristic composite score) |
| `risk_level` | `string` | No | `"High"`, `"Moderate"`, `"Low"`, `"Unknown"` | Simplified risk category for UI badge styling |
| `indicators` | `list[string]` | No | Array of human-readable rationale strings | E.g., `["Original price is 32% above 30-day median", "Product was sold at current price 5 days ago"]` |
| `analysis_message` | `string` | No | Descriptive summary text | User-facing explanatory message |
| `timestamp` | `string` | No | ISO 8601 UTC timestamp | Time analysis was generated |

---

### D. Optional Forecast Fields (Conditional Sub-Object)
Forecast fields are conditionally populated **only** when sufficient historical depth exists ($\ge 14$ daily observations):

| Forecast Field | Type | Nullable? | Description |
|---|---|---|---|
| `forecast_available` | `bool` | No | `true` if $\ge 14$ historical points available; `false` otherwise |
| `forecast_days` | `int` | No | Standardized to `14` days |
| `forecast_points` | `list[ForecastPoint]` | **Yes (`null`)** | Daily predicted price points if `forecast_available == true`, else `null` |
| `forecast_notice` | `string` | No | E.g., `"14-day price trend projection based on historical observations"` or `"Insufficient price history for 14-day forecasting (requires minimum 14 daily points)"` |

---

## 3. Standard JSON Payload Examples

### Example 1: Full Historical Analysis (`Potential Fake Discount`)
```json
{
  "product_name": "UltraSound Wireless Headphones",
  "current_price": 79.99,
  "original_price": 149.99,
  "discount_percentage": 46.7,
  "verdict": "Potential Fake Discount",
  "confidence_score": null,
  "fdi_score": 78.5,
  "risk_level": "High",
  "indicators": [
    "Original reference price ($149.99) is 68.5% higher than 30-day median price ($89.00)",
    "Product was sold at $82.50 seven days before the sale event",
    "Current selling price offers less than 10% genuine savings over 30-day typical price"
  ],
  "analysis_message": "High likelihood of artificial discount markup. The reference price appears inflated immediately prior to the advertised sale.",
  "timestamp": "2026-11-16T20:15:00Z",
  "forecast": {
    "forecast_available": true,
    "forecast_days": 14,
    "forecast_points": [
      {"date": "2026-11-17", "predicted_price": 79.99, "direction": "flat"},
      {"date": "2026-11-18", "predicted_price": 78.50, "direction": "down"}
    ],
    "forecast_notice": "Trend projection based on 45 historical observations."
  }
}
```

### Example 2: Cold-Start Analysis (`Needs More Data`)
```json
{
  "product_name": "New Brand Smart Watch",
  "current_price": 199.00,
  "original_price": 249.00,
  "discount_percentage": 20.1,
  "verdict": "Needs More Data",
  "confidence_score": null,
  "fdi_score": 35.0,
  "risk_level": "Unknown",
  "indicators": [
    "No historical price observations available for baseline calculation",
    "Advertised discount (20.1%) cannot be verified against historical median"
  ],
  "analysis_message": "Insufficient historical data to verify whether this discount is genuine or artificial.",
  "timestamp": "2026-11-16T20:16:00Z",
  "forecast": {
    "forecast_available": false,
    "forecast_days": 14,
    "forecast_points": null,
    "forecast_notice": "Forecasting requires at least 14 days of historical price records."
  }
}
```

---

## 4. Next Steps for Rahul Amin (Backend Developer)

1. Review this provisional schema against planned FastAPI Pydantic models (`BaseModel`).
2. Resolve the route naming discrepancy (`POST /api/analyze` vs `POST /analyze`).
3. Confirm whether `historical_prices` should be submitted in the request body or queried from a local DuckDB cache when a `product_id` is supplied.
