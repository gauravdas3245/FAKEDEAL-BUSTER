import os
import re
from datetime import datetime
from urllib.parse import urlparse

from fastapi import FastAPI, Request, status, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.exceptions import AppException, MLServiceUnavailableError
from app.schemas.request import AnalyzeRequest
from app.schemas.inspection import InspectionRequest
from app.schemas.response import AnalyzeResponse, ErrorResponse, ErrorDetail
from app.schemas.forecast import ForecastRequest
from app.services.analysis_service import AnalysisService
from app.services.product_catalog_service import ProductCatalogService, normalize_identity
from app.services.history_service import HistoryService
from app.services.forecast_service import ForecastService
from app.services.ml_adapter import ARTIFACT_DIRECTORY

# Initialize FastAPI application
app = FastAPI(
    title="FakeDeal Buster API",
    description="Backend API for detecting potentially misleading e-commerce discounts.",
    version="1.0.0"
)

# Configure CORS Middleware
allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if allowed_origins_env.strip():
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the analysis service singleton
analysis_service = AnalysisService()
product_catalog_service = ProductCatalogService()
history_service = HistoryService()
forecast_service = ForecastService(history_service)


# ---------------------------------------------------------------------------
# Exception Handlers (Consistent Error Response Contract)
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles Pydantic request validation errors.
    Returns HTTP 422 with a structured error response matching API_CONTRACT.md.
    """
    error_messages = []
    for err in exc.errors():
        loc = " -> ".join(str(item) for item in err.get("loc", []) if item != "body")
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{loc}: {msg}" if loc else msg)

    full_message = "; ".join(error_messages) if error_messages else "Please provide valid product details."

    error_code = "INVALID_PRODUCT_URL" if any(
        "product_url" in [str(item) for item in err.get("loc", [])] for err in exc.errors()
    ) else "VALIDATION_ERROR"
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=error_code,
            message=full_message
        )
    )
    return JSONResponse(
        status_code=422,
        content=error_payload.model_dump()
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handles custom application domain exceptions (404, 409, 503, etc.).
    Returns structured error responses matching API_CONTRACT.md.
    """
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=exc.code,
            message=exc.message
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump()
    )


@app.exception_handler(ValueError)
async def domain_validation_exception_handler(request: Request, exc: ValueError):
    payload = ErrorResponse(success=False, error=ErrorDetail(code="VALIDATION_ERROR", message=str(exc)))
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(RuntimeError)
async def analysis_exception_handler(request: Request, exc: RuntimeError):
    payload = ErrorResponse(
        success=False,
        error=ErrorDetail(code="ANALYSIS_FAILED", message="ML analysis could not be completed."),
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Fallback handler for any unhandled exceptions.
    Returns HTTP 500 with a consistent error structure.
    """
    error_payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred."
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload.model_dump()
    )


# ---------------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["General"])
def root():
    """Root endpoint welcoming users and indicating server status."""
    return {
        "message": "Welcome to FakeDeal Buster API",
        "status": "running"
    }


@app.get("/health", tags=["General"])
@app.get("/api/health", tags=["General"])
def health_check():
    """Report process health separately from local data/artifact availability."""
    database_ready = history_service.dataset_path.is_file()
    artifact_files = ("isolation_forest.joblib", "preprocessor.json", "metadata.json",
                      "validation_summary.json", "verification_fixture.json", "checksums.sha256")
    artifacts_present = all((ARTIFACT_DIRECTORY / name).is_file() for name in artifact_files)
    synthetic_model_present = (analysis_service.synthetic_classifier.artifact_dir / "checksums.sha256").is_file()
    return {"status": "healthy" if database_ready and artifacts_present else "degraded",
            "process": "healthy", "database": "available" if database_ready else "unavailable",
            "model_bundle": "present_unverified" if artifacts_present else "unavailable",
            "synthetic_classifier_bundle": "present_unverified" if synthetic_model_present else "unavailable",
            "service": "FakeDeal Buster Backend"}


@app.get("/api/catalog", tags=["Product catalog"])
def product_catalog():
    """Expose product metadata from the derived original-dataset catalogue."""
    return product_catalog_service.catalog()


@app.get("/api/catalog/metadata", tags=["Product catalog"])
def product_catalog_metadata():
    """Return supported filters without sending the full product catalogue."""
    catalog = product_catalog_service.catalog()
    return {key: value for key, value in catalog.items() if key != "products"}


@app.get("/api/catalog/search", tags=["Product catalog"])
def search_product_catalog(q: str = Query(default="", max_length=200), category: str = "",
                           platform: str = "", limit: int = Query(default=30, ge=1, le=100)):
    return {"products": product_catalog_service.search(q, category, platform, limit)}


@app.post("/api/inspect", tags=["Analysis"])
def inspect_listing(request: InspectionRequest):
    """Resolve user product metadata, then adapt to the unchanged five-field ML request."""
    supported = product_catalog_service.catalog()
    if request.platform.casefold() not in supported["platforms"]:
        raise AppException("Select a marketplace present in this dataset.", code="INVALID_PLATFORM", status_code=422)
    if request.category.casefold() not in {value.casefold() for value in supported["categories"]}:
        raise AppException("Select a category present in this dataset.", code="INVALID_CATEGORY", status_code=422)
    resolved = None
    asin_match = None
    if request.product_url:
        parsed = urlparse(request.product_url)
        host = (parsed.hostname or "").lower()
        known_domains = {
            "amazon.com": "amazon", "amazon.in": "amazon", "bestbuy.com": "bestbuy",
            "ebay.com": "ebay", "flipkart.com": "flipkart", "walmart.com": "walmart",
        }
        url_platform = next((platform for domain, platform in known_domains.items()
                             if host == domain or host.endswith("." + domain)), None)
        if url_platform and url_platform != request.platform.casefold():
            raise AppException("The URL marketplace does not match the selected platform.",
                               code="INVALID_PLATFORM", status_code=422)
        if host == "amazon.com" or host.endswith(".amazon.com") or host.endswith(".amazon.in") or host == "amazon.in":
            match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?]|$)", parsed.path, re.I)
            if match:
                asin_rows = product_catalog_service.resolve_asin(match.group(1), request.platform)
                if not asin_rows:
                    from app.exceptions import ProductNotFoundError
                    raise ProductNotFoundError("This Amazon product identifier is not present in the dataset.")
                exact = [row for row in asin_rows
                         if row["product_id"] == (request.selected_product_id or row["product_id"])
                         and row["category"].casefold() == request.category.casefold()
                         and normalize_identity(row["title"]) == normalize_identity(request.product_name)]
                if not exact:
                    from app.exceptions import ProductNotFoundError
                    raise ProductNotFoundError("The product name, category, marketplace, and URL identifier do not identify the same dataset product.")
                if len(exact) > 1:
                    return {"status": "AMBIGUOUS_PRODUCT", "selection_possible": False, "candidates": []}
                resolved = {"status": "RESOLVED", **exact[0]}
                asin_match = True
    if resolved is None:
        resolved = product_catalog_service.resolve(
            request.product_name, request.platform, request.category, request.selected_product_id
        )
    if resolved["status"] == "AMBIGUOUS_PRODUCT":
        return resolved
    as_of = request.as_of or datetime.now()
    ml_request = AnalyzeRequest(
        product_id=resolved["product_id"],
        platform=resolved["platform"],
        as_of=as_of,
        current_price=request.current_price,
        original_price=request.original_price,
    )
    analysis = analysis_service.analyze(ml_request, category=resolved["category"])
    price_history = history_service.actual_history(resolved["product_id"], resolved["platform"], as_of, 365)
    historical_summary = history_service.historical_summary(resolved["product_id"], resolved["platform"], as_of)
    cross_platform = history_service.cross_platform(resolved["product_id"], as_of)
    return {
        "status": "ANALYZED",
        "assessment_verdict": analysis.assessment_verdict,
        "assessment_explanation": analysis.assessment_explanation,
        "product": {
            "title": resolved["title"],
            "category": resolved["category"],
            "platform": resolved["platform"],
            "brand": resolved["brand"],
            "subcategory": resolved.get("subcategory"),
            "asin": resolved.get("asin") or None,
        },
        "url_mapping_supported": bool(asin_match),
        "price_history": price_history,
        "historical_summary": historical_summary,
        "cross_platform": cross_platform,
        "forecast": forecast_service.forecast(resolved["product_id"], resolved["platform"], as_of),
        "analysis": analysis.model_dump(mode="json"),
    }


@app.post("/api/forecast", tags=["Forecast"])
def forecast_product(request: ForecastRequest):
    """Return a baseline 14-day forecast only when backtestable daily history exists."""
    return forecast_service.forecast(request.product_id, request.platform, request.as_of)


@app.get("/api/models/synthetic-comparison", tags=["Synthetic experiment"])
def synthetic_model_comparison():
    """Expose synthetic held-out comparison metrics with explicit scope."""
    return analysis_service.synthetic_classifier.comparison()


@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    responses={
        200: {"model": AnalyzeResponse, "description": "Successful analysis (including NEEDS_MORE_DATA)"},
        404: {"model": ErrorResponse, "description": "Product or platform records not found"},
        409: {"model": ErrorResponse, "description": "Conflicting duplicate historical records"},
        422: {"model": ErrorResponse, "description": "Request validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Verified ML artifact bundle unavailable"},
    },
    tags=["Analysis"]
)
def analyze_product(request: AnalyzeRequest):
    """
    Analyzes an e-commerce product discount using historical price patterns.
    Computes rolling features, checks data sufficiency, and returns risk assessments.
    """
    category = product_catalog_service.category_for(request.product_id, request.platform)
    return analysis_service.analyze(request, category=category)
