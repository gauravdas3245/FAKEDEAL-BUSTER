from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AnalyzeRequest(BaseModel):
    """The public analysis request has exactly five required fields."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    as_of: datetime
    current_price: float = Field(gt=0, allow_inf_nan=False)
    original_price: float = Field(gt=0, allow_inf_nan=False)

    @field_validator("product_id", "platform", mode="before")
    @classmethod
    def require_non_whitespace(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()

    @field_validator("current_price", "original_price", mode="before")
    @classmethod
    def reject_boolean_prices(cls, value):
        if isinstance(value, bool):
            raise ValueError("must be a positive finite number")
        return value

    @field_validator("as_of")
    @classmethod
    def reject_future_timestamp(cls, value: datetime):
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value > now:
            raise ValueError("as_of cannot be in the future")
        return value

    @model_validator(mode="after")
    def current_price_must_not_exceed_original(self):
        if self.current_price > self.original_price:
            raise ValueError("current_price cannot exceed original_price")
        return self
