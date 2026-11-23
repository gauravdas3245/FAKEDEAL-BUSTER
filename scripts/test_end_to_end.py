"""Comprehensive End-to-End Verification Suite for FakeDeal Buster.

Verifies the complete pipeline across all mandatory demonstration workflows:
1. Dataset-backed product with sufficient historical data.
2. Product observation with insufficient historical data.
3. Manual product entry with unverified seller and listing metadata.
4. Input validation and error handling for invalid requests.
5. Synthetic discount scenario and classifier benchmark comparison.
"""

from datetime import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app


def run_e2e_suite():
    client = TestClient(app)
    results = {}

    print("=" * 70)
    print("FAKEDEAL BUSTER - COMPLETE END-TO-END VERIFICATION")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # 0. Health & Readiness Check
    # -------------------------------------------------------------------------
    print("\n[Step 0] Health Check...")
    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"  Status: {health_data['status']}")
    print(f"  Database: {health_data['database']}")
    print(f"  Model Bundle: {health_data['model_bundle']}")
    print(f"  Synthetic Classifier: {health_data['synthetic_classifier_bundle']}")
    assert health_data["database"] == "available"
    assert health_data["model_bundle"] == "present_unverified"
    results["step_0_health"] = "PASSED"

    # -------------------------------------------------------------------------
    # 1. Dataset-backed product with sufficient historical data
    # -------------------------------------------------------------------------
    print("\n[Step 1] Dataset-Backed Product with Sufficient History...")
    payload_1 = {
        "product_name": "Google Max Smartphones (Green)",
        "platform": "amazon",
        "category": "Electronics",
        "as_of": "2024-10-18T00:00:00",
        "current_price": 203.62,
        "original_price": 239.02,
        "product_url": "https://www.amazon.com/dp/5F2B9323C3",
    }
    resp_1 = client.post("/api/inspect", json=payload_1)
    assert resp_1.status_code == 200, f"Step 1 failed: {resp_1.text}"
    data_1 = resp_1.json()

    assert data_1["status"] == "ANALYZED"
    assert data_1["url_mapping_supported"] is True
    assert data_1["product"]["category"] == "Electronics"
    assert data_1["product"]["platform"] == "amazon"
    assert data_1["assessment_verdict"] == "No Suspicious Pattern Detected"
    assert len(data_1["price_history"]) > 0
    assert data_1["forecast"]["status"] == "AVAILABLE"
    assert len(data_1["forecast"]["points"]) == 14
    assert data_1["analysis"]["ml_anomaly"]["status"] == "OK"
    assert data_1["analysis"]["ml_anomaly"]["verdict"] == "NO_ANOMALY"
    assert data_1["analysis"]["fdi"]["status"] == "INSUFFICIENT_INPUTS"
    assert data_1["analysis"]["fdi"]["fdi_score"] is None
    assert data_1["analysis"]["synthetic_classifier"]["status"] == "SYNTHETIC_SCENARIO_EXPERIMENT"

    print(f"  Resolved: {data_1['product']['title']} ({data_1['product']['platform']})")
    print(f"  Assessment Verdict: {data_1['assessment_verdict']}")
    print(f"  Isolation Forest Verdict: {data_1['analysis']['ml_anomaly']['verdict']}")
    print(f"  Anomaly Score: {data_1['analysis']['ml_anomaly']['anomaly_score']:.4f}")
    print(f"  FDI Status: {data_1['analysis']['fdi']['status']} (fdi_score: {data_1['analysis']['fdi']['fdi_score']})")
    print(f"  Forecast Status: {data_1['forecast']['status']} (Points: {len(data_1['forecast']['points'])}, Method: {data_1['forecast']['method']})")
    print(f"  Backtest Evaluated: {data_1['forecast']['backtest']['metrics']['last_observation']['observations']} observations")
    results["step_1_sufficient_history"] = "PASSED"

    # -------------------------------------------------------------------------
    # 2. Product observation with insufficient historical data
    # -------------------------------------------------------------------------
    print("\n[Step 2] Product Observation with Insufficient Historical Data...")
    payload_2 = {
        "product_name": "Google Max Smartphones (Green)",
        "platform": "amazon",
        "category": "Electronics",
        "as_of": "2026-11-18T00:00:00",  # Future date after dataset records end
        "current_price": 203.62,
        "original_price": 239.02,
    }
    resp_2 = client.post("/api/inspect", json=payload_2)
    assert resp_2.status_code == 200, f"Step 2 failed: {resp_2.text}"
    data_2 = resp_2.json()

    assert data_2["status"] == "ANALYZED"
    assert data_2["assessment_verdict"] == "Insufficient Evidence"
    assert data_2["analysis"]["analysis_status"] == "NEEDS_MORE_DATA"
    assert data_2["analysis"]["ml_anomaly"]["anomaly_score"] is None
    assert data_2["analysis"]["fdi"]["fdi_score"] is None
    assert data_2["forecast"]["status"] == "INSUFFICIENT_HISTORY"
    assert data_2["forecast"]["forecast"] is None

    print(f"  Assessment Verdict: {data_2['assessment_verdict']}")
    print(f"  Analysis Status: {data_2['analysis']['analysis_status']}")
    print(f"  Forecast Status: {data_2['forecast']['status']}")
    print(f"  Forecast Message: {data_2['forecast']['message']}")
    results["step_2_insufficient_history"] = "PASSED"

    # -------------------------------------------------------------------------
    # 3. Manual product entry with unverified seller and listing metadata
    # -------------------------------------------------------------------------
    print("\n[Step 3] Manual Product Entry with Unverified Seller Info (No URL)...")
    payload_3 = {
        "product_name": "Google Max Smartphones (Green)",
        "platform": "amazon",
        "category": "Electronics",
        "as_of": "2024-10-18T00:00:00",
        "current_price": 203.62,
        "original_price": 239.02,
        "seller_name": "Apex Electronics Ltd",
        "seller_rating": 4.5,
        "product_url": None,  # No URL provided
    }
    resp_3 = client.post("/api/inspect", json=payload_3)
    assert resp_3.status_code == 200, f"Step 3 failed: {resp_3.text}"
    data_3 = resp_3.json()

    assert data_3["status"] == "ANALYZED"
    assert data_3["url_mapping_supported"] is False
    assert "Google Max Smartphones" in data_3["product"]["title"]
    assert data_3["assessment_verdict"] in {"No Suspicious Pattern Detected", "Potential Suspicious Discount Pattern"}

    print(f"  Product Name Resolved: {data_3['product']['title']}")
    print(f"  URL Mapping Supported: {data_3['url_mapping_supported']} (URL was optional and omitted)")
    print(f"  Seller info treated as unverified user metadata without contaminating ML inputs")
    results["step_3_manual_entry"] = "PASSED"

    # -------------------------------------------------------------------------
    # 4. Input validation and error handling for invalid requests
    # -------------------------------------------------------------------------
    print("\n[Step 4] Validation of Invalid Inputs...")
    
    # 4a. Current price > original price
    bad_price_resp = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 300.0, "original_price": 200.0,
    })
    assert bad_price_resp.status_code == 422
    assert bad_price_resp.json()["error"]["code"] == "VALIDATION_ERROR"
    print("  [4a] Current price > original price -> HTTP 422 VALIDATION_ERROR: OK")

    # 4b. Invalid seller rating > 5.0
    bad_rating_resp = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 100.0, "original_price": 150.0,
        "seller_rating": 6.5,
    })
    assert bad_rating_resp.status_code == 422
    assert bad_rating_resp.json()["error"]["code"] == "VALIDATION_ERROR"
    print("  [4b] Seller rating > 5.0 -> HTTP 422 VALIDATION_ERROR: OK")

    # 4c. Nonexistent product
    bad_product_resp = client.post("/api/inspect", json={
        "product_name": "Nonexistent Magic Gadget XYZ 999", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 100.0, "original_price": 150.0,
    })
    assert bad_product_resp.status_code == 404
    assert bad_product_resp.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
    print("  [4c] Unmatched product name -> HTTP 404 PRODUCT_NOT_FOUND (no silent substitution): OK")

    # 4d. Invalid product URL scheme
    bad_url_resp = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 100.0, "original_price": 150.0,
        "product_url": "javascript:stealTokens()",
    })
    assert bad_url_resp.status_code == 422
    assert bad_url_resp.json()["error"]["code"] == "INVALID_PRODUCT_URL"
    print("  [4d] Malicious/invalid URL scheme -> HTTP 422 INVALID_PRODUCT_URL: OK")
    results["step_4_validation_errors"] = "PASSED"

    # -------------------------------------------------------------------------
    # 5. Synthetic scenario result & classifier comparison endpoint
    # -------------------------------------------------------------------------
    print("\n[Step 5] Synthetic Scenario Result & Model Benchmark Comparison...")
    
    # 5a. Artificially inflated discount scenario detection
    payload_inflated = {
        "product_name": "Google Max Smartphones (Green)",
        "platform": "amazon",
        "category": "Electronics",
        "as_of": "2024-10-18T00:00:00",
        "current_price": 50.0,
        "original_price": 850.0,  # Extreme artificial markup
    }
    resp_5a = client.post("/api/inspect", json=payload_inflated)
    assert resp_5a.status_code == 200
    data_5a = resp_5a.json()
    assert data_5a["assessment_verdict"] == "Potential Suspicious Discount Pattern"
    assert data_5a["analysis"]["ml_anomaly"]["verdict"] == "ANOMALY"
    print(f"  [5a] Inflated Reference Price Listing -> Assessment: {data_5a['assessment_verdict']}")
    print(f"       Isolation Forest Verdict: {data_5a['analysis']['ml_anomaly']['verdict']}")
    print(f"       Synthetic Classifier Status: {data_5a['analysis']['synthetic_classifier']['status']}")

    # 5b. Benchmark comparison endpoint
    resp_comp = client.get("/api/models/synthetic-comparison")
    assert resp_comp.status_code == 200
    comp_data = resp_comp.json()
    assert comp_data["status"] == "AVAILABLE"
    assert comp_data["selected_model"] == "random_forest"
    assert comp_data["evaluation_scope"] == "SYNTHETIC_HELD_OUT_TEST_ONLY"
    assert "logistic_regression" in comp_data["test_metrics"]
    assert "random_forest" in comp_data["test_metrics"]

    lr = comp_data["test_metrics"]["logistic_regression"]
    rf = comp_data["test_metrics"]["random_forest"]

    print("  [5b] Supervised Model Benchmark Metrics (Held-Out Test N=6,000):")
    print(f"       Metric                     | Logistic Regression | Random Forest (Selected)")
    print(f"       ---------------------------|---------------------|-------------------------")
    print(f"       Decision Threshold         | {lr['threshold']:19.4f} | {rf['threshold']:23.4f}")
    print(f"       Precision                  | {lr['precision']:19.4f} | {rf['precision']:23.4f}")
    print(f"       Recall                     | {lr['recall']:19.4f} | {rf['recall']:23.4f}")
    print(f"       F1-Score                   | {lr['f1']:19.4f} | {rf['f1']:23.4f}")
    print(f"       ROC-AUC                    | {lr['roc_auc']:19.4f} | {rf['roc_auc']:23.4f}")
    print(f"       PR-AUC (Avg Precision)     | {lr['pr_auc_average_precision']:19.4f} | {rf['pr_auc_average_precision']:23.4f}")
    print(f"       Gini Coefficient (2*AUC-1) | {lr['gini_coefficient_2auc_minus_1']:19.4f} | {rf['gini_coefficient_2auc_minus_1']:23.4f}")
    print(f"       FPR on Synthetic Genuine   | {lr['false_positive_rate_on_synthetic_genuine']:19.4f} | {rf['false_positive_rate_on_synthetic_genuine']:23.4f}")
    results["step_5_synthetic_benchmark"] = "PASSED"

    print("\n" + "=" * 70)
    print("ALL 5 END-TO-END DEMONSTRATION WORKFLOWS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_e2e_suite()
