"""Deterministic retry/backoff policy primitives."""

from pydantic import BaseModel, ConfigDict, Field


class RetryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_attempts: int = Field(default=5, ge=1)
    initial_delay_seconds: float = Field(default=1.0, gt=0)
    max_delay_seconds: float = Field(default=60.0, gt=0)
    multiplier: float = Field(default=2.0, ge=1.0)

    def delay_seconds(self, retry_number: int) -> float:
        if retry_number < 1:
            raise ValueError("retry_number must be >= 1")
        return min(
            self.initial_delay_seconds * self.multiplier ** (retry_number - 1),
            self.max_delay_seconds,
        )
