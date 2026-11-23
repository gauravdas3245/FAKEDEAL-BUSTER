from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(min_length=1, max_length=100)
    platform: str = Field(min_length=1, max_length=40)
    as_of: datetime

    @field_validator("product_id", "platform")
    @classmethod
    def trim_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

    @field_validator("as_of")
    @classmethod
    def disallow_future(cls, value: datetime) -> datetime:
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value > now:
            raise ValueError("as_of cannot be in the future")
        return value
