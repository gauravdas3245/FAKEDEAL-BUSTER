"""
Custom domain exceptions for the FakeDeal Buster backend.
All exceptions carry an HTTP status code and a contract-compliant machine-readable error code.
"""

class AppException(Exception):
    """Base application exception with HTTP status code and error code."""
    def __init__(self, message: str, code: str = "INTERNAL_SERVER_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ProductNotFoundError(AppException):
    """Raised when a product or platform combination has no records."""
    def __init__(self, message: str = "Product or platform records not found in historical data."):
        super().__init__(message=message, code="PRODUCT_NOT_FOUND", status_code=404)


class HistoryConflictError(AppException):
    """Raised when conflicting price records exist for the same product, platform, and date."""
    def __init__(self, message: str = "Conflicting duplicate historical records detected for this product and date."):
        super().__init__(message=message, code="HISTORY_CONFLICT", status_code=409)


class MLServiceUnavailableError(AppException):
    """Raised when an ML prediction is required but the ML service or model is unavailable."""
    def __init__(self, message: str = "Machine learning scoring service is currently unavailable."):
        super().__init__(message=message, code="ML_SERVICE_UNAVAILABLE", status_code=503)


class DatasetUnavailableError(AppException):
    """Raised when the derived, verified runtime dataset is missing or unreadable."""
    def __init__(self, message: str = "The product catalogue and historical dataset are currently unavailable."):
        super().__init__(message=message, code="DATASET_UNAVAILABLE", status_code=503)
