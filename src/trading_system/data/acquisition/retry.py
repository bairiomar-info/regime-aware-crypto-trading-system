"""Deterministic retry/backoff policy primitives."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RetryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_attempts: int = Field(default=5, ge=1)
    initial_delay_seconds: Decimal = Field(default=Decimal("1"), gt=0)
    max_delay_seconds: Decimal = Field(default=Decimal("60"), gt=0)
    multiplier: Decimal = Field(default=Decimal("2"), ge=1)

    def delay_seconds(self, retry_number: int) -> Decimal:
        if retry_number < 1:
            raise ValueError("retry_number must be >= 1")
        return min(self.initial_delay_seconds * self.multiplier ** (retry_number - 1), self.max_delay_seconds)
