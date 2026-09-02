"""Versioned policy contracts for point-in-time universe construction."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UniversePolicy(BaseModel):
    """Immutable, versioned rules used to construct a research universe.

    The policy describes eligibility rules only. It does not contain historical
    observations, and therefore cannot silently turn present-day information
    into historical eligibility.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    policy_id: str = Field(min_length=1)
    version: str = Field(
        pattern=r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
    )
    allowed_market_types: tuple[str, ...] = ("spot",)
    allowed_quote_assets: tuple[str, ...] = ("USDT",)
    excluded_classifications: tuple[str, ...] = ()
    minimum_history_bars: int = Field(default=0, ge=0)
    minimum_quote_volume: str | None = None

    @field_validator(
        "allowed_market_types",
        "allowed_quote_assets",
        "excluded_classifications",
    )
    @classmethod
    def normalize_values(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(value.upper() for value in values)

    @field_validator("minimum_quote_volume")
    @classmethod
    def validate_quote_volume(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("minimum_quote_volume must not be blank")
        return value.strip()
