from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InspectionRequest(BaseModel):
    """User-facing product metadata adapted to the unchanged five-field ML API."""

    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(min_length=1, max_length=200)
    platform: str = Field(min_length=1, max_length=40)
    category: str = Field(min_length=1, max_length=100)
    as_of: Optional[datetime] = None
    current_price: float = Field(gt=0, allow_inf_nan=False)
    original_price: float = Field(gt=0, allow_inf_nan=False)
    seller_name: Optional[str] = Field(default=None, max_length=120)
    seller_rating: Optional[float] = Field(default=None, ge=1, le=5, allow_inf_nan=False)
    product_url: Optional[str] = Field(default=None, max_length=2048)
    selected_product_id: Optional[str] = Field(default=None, min_length=1, max_length=100)

    @field_validator("product_name", "platform", "category", mode="before")
    @classmethod
    def trim_required_text(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()

    @field_validator("current_price", "original_price", mode="before")
    @classmethod
    def reject_boolean_prices(cls, value):
        if isinstance(value, bool):
            raise ValueError("price must be a positive finite number")
        return value

    @field_validator("seller_name", mode="before")
    @classmethod
    def normalize_seller_name(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("seller_name must be text")
        value = value.strip()
        return value or None

    @field_validator("seller_rating", mode="before")
    @classmethod
    def validate_rating(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise ValueError("seller_rating must be between 1.0 and 5.0")
        return value

    @field_validator("product_url", mode="before")
    @classmethod
    def validate_http_url(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("product_url must be text")
        value = value.strip()
        if not value:
            return None
        parsed = urlparse(value)
        try:
            hostname = parsed.hostname
            parsed.port  # Force validation of malformed numeric ports.
        except ValueError as exc:
            raise ValueError("product_url must be a valid HTTP or HTTPS URL") from exc
        if parsed.scheme.lower() not in {"http", "https"} or not hostname or any(character.isspace() for character in value):
            raise ValueError("product_url must be a valid HTTP or HTTPS URL")
        return value

    @field_validator("as_of")
    @classmethod
    def reject_future_timestamp(cls, value: Optional[datetime]):
        if value is None:
            return None
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value > now:
            raise ValueError("as_of cannot be in the future")
        return value

    @model_validator(mode="after")
    def validate_price_pair(self):
        if self.current_price > self.original_price:
            raise ValueError("current_price cannot exceed original_price")
        return self
