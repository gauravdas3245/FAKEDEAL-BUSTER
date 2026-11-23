import csv
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app, product_catalog_service
from app.exceptions import DatasetUnavailableError
from app.schemas.inspection import InspectionRequest
from app.services.product_catalog_service import ProductCatalogService


def write_catalog(path, records):
    fields = ["product_id", "title", "category", "platform", "brand", "asin", "timestamp", "price"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def test_full_dataset_catalog_uses_actual_metadata():
    catalog = product_catalog_service.catalog()
    assert catalog["product_count"] in {98, 9980}
    assert len(catalog["products"]) >= catalog["product_count"]
    assert set(catalog["platforms"]) == {"amazon", "bestbuy", "ebay", "flipkart", "walmart"}
    assert set(catalog["categories"]) == {"Appliances", "Books", "Electronics", "Fashion", "Gaming", "Household", "Sports"}
    assert catalog["date_range"] == {"start": "2023-01-01", "end": "2024-12-30"}
    assert catalog["url_mapping_supported"] is False
    assert catalog["amazon_asin_mapping_supported"] is True


def test_search_api_returns_bounded_filter_consistent_real_catalogue_rows():
    client = TestClient(app)
    metadata = client.get("/api/catalog/metadata")
    assert metadata.status_code == 200
    meta = metadata.json()
    assert "products" not in meta
    assert len(meta["platforms"]) == 5
    assert len(meta["categories"]) == 7
    response = client.get("/api/catalog/search", params={
        "q": "Google", "category": "Electronics", "platform": "amazon", "limit": 7,
    })
    assert response.status_code == 200
    results = response.json()["products"]
    assert 0 < len(results) <= 7
    assert all(row["category"] == "Electronics" and row["platform"] == "amazon" for row in results)


def test_real_dataset_forecast_route_emits_validated_curve_or_insufficient_state():
    response = TestClient(app).post("/api/forecast", json={
        "product_id": "P0000001", "platform": "amazon", "as_of": "2024-10-18T00:00:00",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] in {"AVAILABLE", "INSUFFICIENT_HISTORY"}
    if body["status"] == "AVAILABLE":
        assert len(body["points"]) == 14
        assert body["backtest"]["metrics"]["last_observation"]["observations"] == 70
    else:
        assert body["forecast"] is None
        assert body["message"]


def test_full_dataset_resolver_uses_actual_product_and_amazon_identifier():
    service = ProductCatalogService()
    result = service.resolve(" Google Max Smartphones (Green) ", "amazon", "Electronics")
    assert result["product_id"] == "P0000001"
    assert result["asin"] == "5F2B9323C3"
    assert [row["product_id"] for row in service.resolve_asin("5f2b9323c3")] == ["P0000001"]


def test_corrupt_catalog_store_returns_structured_dataset_unavailable(tmp_path):
    corrupt = tmp_path / "broken.duckdb"
    corrupt.write_text("not a DuckDB file", encoding="utf-8")
    with pytest.raises(DatasetUnavailableError) as error:
        ProductCatalogService(corrupt).catalog()
    assert error.value.code == "DATASET_UNAVAILABLE"
    assert str(corrupt) not in error.value.message


def test_unique_normalized_name_platform_category_resolves(tmp_path):
    dataset = tmp_path / "catalog.csv"
    write_catalog(dataset, [{"product_id": "p1", "title": "Example  Phone", "category": "Electronics", "platform": "amazon", "brand": "Acme", "asin": "A1", "timestamp": "2024-01-01T00:00:00", "price": 1}])
    result = ProductCatalogService(dataset).resolve(" example phone ", "AMAZON", " electronics ")
    assert result["status"] == "RESOLVED"
    assert result["product_id"] == "P1"


def test_multiple_actual_matches_require_explicit_selection(tmp_path):
    dataset = tmp_path / "catalog.csv"
    common = {"title": "Example Phone", "category": "Electronics", "platform": "amazon", "timestamp": "2024-01-01T00:00:00", "price": 1}
    write_catalog(dataset, [dict(common, product_id="P1", brand="Acme", asin="A1"), dict(common, product_id="P2", brand="Acme", asin="A2")])
    service = ProductCatalogService(dataset)
    ambiguous = service.resolve("Example Phone", "amazon", "Electronics")
    assert ambiguous["status"] == "AMBIGUOUS_PRODUCT"
    assert {item["asin"] for item in ambiguous["candidates"]} == {"A1", "A2"}
    assert service.resolve("Example Phone", "amazon", "Electronics", "P2")["product_id"] == "P2"


def test_indistinguishable_matches_cannot_be_safely_selected(tmp_path):
    dataset = tmp_path / "catalog.csv"
    common = {"title": "Example Phone", "category": "Electronics", "platform": "amazon", "timestamp": "2024-01-01T00:00:00", "price": 1}
    write_catalog(dataset, [dict(common, product_id="P1"), dict(common, product_id="P2")])
    result = ProductCatalogService(dataset).resolve("Example Phone", "amazon", "Electronics")
    assert result["status"] == "AMBIGUOUS_PRODUCT"
    assert result["selection_possible"] is False


@pytest.mark.parametrize(("name", "platform", "category"), [
    ("Missing", "amazon", "Electronics"),
    ("Example Phone", "ebay", "Electronics"),
    ("Example Phone", "amazon", "Toys"),
])
def test_unmatched_name_platform_or_category_does_not_substitute(tmp_path, name, platform, category):
    dataset = tmp_path / "catalog.csv"
    write_catalog(dataset, [{"product_id": "P1", "title": "Example Phone", "category": "Electronics", "platform": "amazon", "timestamp": "2024-01-01T00:00:00", "price": 1}])
    with pytest.raises(Exception) as error:
        ProductCatalogService(dataset).resolve(name, platform, category)
    assert getattr(error.value, "code", None) == "PRODUCT_NOT_FOUND"


@pytest.mark.parametrize("rating", [1, 5, 4.2, 4.8, None, ""])
def test_seller_rating_accepts_supported_values(rating):
    request = InspectionRequest(product_name="Phone", platform="amazon", category="Electronics",
                                as_of=datetime(2024, 10, 18), current_price=10, original_price=12,
                                seller_rating=rating)
    assert request.seller_rating is None if rating in (None, "") else request.seller_rating == float(rating)


@pytest.mark.parametrize("rating", [0, 5.1, -1, "not-a-rating"])
def test_seller_rating_rejects_invalid_values(rating):
    with pytest.raises(ValueError):
        InspectionRequest(product_name="Phone", platform="amazon", category="Electronics",
                          as_of=datetime(2024, 10, 18), current_price=10, original_price=12,
                          seller_rating=rating)


@pytest.mark.parametrize("url", ["https://shop.example/item", "http://shop.example/item"])
def test_product_url_accepts_http_schemes(url):
    request = InspectionRequest(product_name="Phone", platform="amazon", category="Electronics",
                                as_of=datetime(2024, 10, 18), current_price=10, original_price=12,
                                product_url=url)
    assert request.product_url == url


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "data:text/plain,x", "ftp://shop.example/item", "not a url"])
def test_product_url_rejects_unsupported_or_invalid_schemes(url):
    with pytest.raises(ValueError):
        InspectionRequest(product_name="Phone", platform="amazon", category="Electronics",
                          as_of=datetime(2024, 10, 18), current_price=10, original_price=12,
                          product_url=url)


def test_product_inspection_calls_real_model_without_exposing_internal_id():
    client = TestClient(app)
    response = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 203.62, "original_price": 239.02,
        "seller_name": "  Example Seller  ", "seller_rating": 4.8, "product_url": "https://shop.example/item",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ANALYZED"
    assert "product_id" not in body["product"]
    assert body["url_mapping_supported"] is False
    assert body["analysis"]["ml_anomaly"]["status"] == "OK"
    assert body["analysis"]["ml_anomaly"]["model_version"] == "isolation_forest_v1"
    assert list(body["analysis"]["ml_anomaly"]["features"]) == [
        "msrp_to_30d_avg", "ratio_to_30d_avg", "price_volatility_30d", "recent_7d_surge"
    ]
    assert body["assessment_verdict"] in {
        "Potential Suspicious Discount Pattern",
        "No Suspicious Pattern Detected",
        "Insufficient Evidence",
    }
    assert body["assessment_explanation"]
    assert body["analysis"]["fdi"]["status"] == "INSUFFICIENT_INPUTS"
    assert body["analysis"]["fdi"]["fdi_score"] is None
    assert body["analysis"]["synthetic_classifier"]["status"] == "SYNTHETIC_SCENARIO_EXPERIMENT"
    assert "not a real-world fraud prediction" in body["analysis"]["synthetic_classifier"]["disclaimer"]
    assert len(body["price_history"]) > 0
    assert body["historical_summary"]["observation_count"] >= 14
    assert len(body["cross_platform"]) >= 4
    assert body["forecast"]["status"] == "AVAILABLE"
    assert len(body["forecast"]["points"]) == 14
    assert body["assessment_verdict"] in {
        "Potential Suspicious Discount Pattern",
        "No Suspicious Pattern Detected",
        "Insufficient Evidence",
    }
    assert body["assessment_explanation"]
    assert body["analysis"]["fdi"]["status"] == "INSUFFICIENT_INPUTS"


def test_synthetic_comparison_route_marks_held_out_metrics_as_synthetic_only():
    response = TestClient(app).get("/api/models/synthetic-comparison")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "AVAILABLE"
    assert body["evaluation_scope"] == "SYNTHETIC_HELD_OUT_TEST_ONLY"
    assert "not real-world fraud metrics" in body["disclaimer"]
    assert set(body["test_metrics"]) == {"logistic_regression", "random_forest"}
    assert all(metrics["support"]["synthetic_genuine"] > 0 for metrics in body["test_metrics"].values())


def test_amazon_url_uses_only_exact_dataset_asin_mapping():
    response = TestClient(app).post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 203.62, "original_price": 239.02,
        "product_url": "https://www.amazon.com/dp/5F2B9323C3",
    })
    assert response.status_code == 200, response.text
    assert response.json()["url_mapping_supported"] is True


def test_recognized_url_marketplace_must_match_selected_platform():
    response = TestClient(app).post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 203.62, "original_price": 239.02,
        "product_url": "https://www.ebay.com/item/123",
    })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PLATFORM"


def test_invalid_product_url_has_specific_structured_error():
    response = TestClient(app).post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 203.62, "original_price": 239.02,
        "product_url": "javascript:alert(1)",
    })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PRODUCT_URL"


@pytest.mark.parametrize(("field", "value", "code"), [
    ("platform", "unsupported", "INVALID_PLATFORM"),
    ("category", "Not A Dataset Category", "INVALID_CATEGORY"),
])
def test_unsupported_dataset_metadata_has_structured_error(field, value, code):
    payload = {"product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
               "as_of": "2024-10-18T00:00:00", "current_price": 203.62, "original_price": 239.02}
    response = TestClient(app).post("/api/inspect", json={**payload, field: value})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == code


def test_product_inspection_reports_needs_more_data_for_current_date():
    client = TestClient(app)
    response = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2026-11-18T00:00:00", "current_price": 203.62, "original_price": 239.02,
    })
    assert response.status_code == 200, response.text
    analysis = response.json()["analysis"]
    assert response.json()["assessment_verdict"] == "Insufficient Evidence"
    assert "Insufficient historical price observations" in response.json()["assessment_explanation"]
    assert analysis["analysis_status"] == "NEEDS_MORE_DATA"
    assert analysis["assessment_verdict"] == "Insufficient Evidence"
    assert analysis["ml_anomaly"]["anomaly_score"] is None
    assert analysis["fdi"]["fdi_score"] is None


def test_product_inspection_verdict_states_distinguished():
    client = TestClient(app)
    # Normal listing -> No Suspicious Pattern Detected
    resp_normal = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 203.62, "original_price": 239.02,
    })
    assert resp_normal.status_code == 200
    assert resp_normal.json()["assessment_verdict"] == "No Suspicious Pattern Detected"

    # Extreme price distortion / anomaly -> Potential Suspicious Discount Pattern
    resp_anomaly = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2024-10-18T00:00:00", "current_price": 50.0, "original_price": 850.0,
    })
    assert resp_anomaly.status_code == 200
    assert resp_anomaly.json()["assessment_verdict"] == "Potential Suspicious Discount Pattern"

    # Future date / missing history -> Insufficient Evidence
    resp_insufficient = client.post("/api/inspect", json={
        "product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
        "as_of": "2026-11-18T00:00:00", "current_price": 203.62, "original_price": 239.02,
    })
    assert resp_insufficient.status_code == 200
    assert resp_insufficient.json()["assessment_verdict"] == "Insufficient Evidence"


def test_product_inspection_validation_errors():
    client = TestClient(app)
    payload = {"product_name": "Google Max Smartphones (Green)", "platform": "amazon", "category": "Electronics",
               "as_of": "2024-10-18T00:00:00", "current_price": 203.62, "original_price": 239.02}
    bad_rating = client.post("/api/inspect", json={**payload, "seller_rating": 5.1})
    assert bad_rating.status_code == 422
    assert bad_rating.json()["error"]["code"] == "VALIDATION_ERROR"
    bad_price = client.post("/api/inspect", json={**payload, "current_price": 240})
    assert bad_price.status_code == 422
    invalid_name = client.post("/api/inspect", json={**payload, "product_name": "Nonexistent"})
    assert invalid_name.status_code == 404
    assert invalid_name.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_internal_analysis_endpoint_rejects_future_timestamp():
    client = TestClient(app)
    response = client.post("/api/analyze", json={
        "product_id": "P0000001", "platform": "amazon", "as_of": "2099-01-01T00:00:00",
        "current_price": 203.62, "original_price": 239.02,
    })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
