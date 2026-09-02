"""Point-in-time research universe domain models."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MembershipStatus(StrEnum):
    """Historical state of an exchange instrument."""

    NOT_LISTED = "not_listed"
    LISTED = "listed"
    TRADABLE = "tradable"
    DELISTED = "delisted"
    HALTED = "halted"


class EligibilityReason(StrEnum):
    """Machine-readable reasons for a research-universe decision."""

    ELIGIBLE = "eligible"
    NOT_LISTED = "not_listed"
    DELISTED = "delisted"
    NOT_TRADABLE = "not_tradable"
    WRONG_MARKET_TYPE = "wrong_market_type"
    DISALLOWED_QUOTE_ASSET = "disallowed_quote_asset"
    EXCLUDED_CLASSIFICATION = "excluded_classification"
    INSUFFICIENT_HISTORY = "insufficient_history"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    FUTURE_INFORMATION = "future_information"


class PointInTimeMembership(BaseModel):
    """Immutable historical membership interval for one exchange instrument."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    instrument_id: str = Field(min_length=1)
    effective_from: datetime
    effective_to: datetime | None = None
    status: MembershipStatus
    source: str = Field(min_length=1)
    source_available_at: datetime | None = None

    @field_validator("effective_from", "effective_to", "source_available_at")
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("membership timestamps must be UTC-aware")
        return value

    @model_validator(mode="after")
    def validate_interval(self) -> "PointInTimeMembership":
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        if (
            self.source_available_at is not None
            and self.source_available_at > self.effective_from
        ):
            raise ValueError("source_available_at cannot be after effective_from")
        return self


class EligibilityDecision(BaseModel):
    """Immutable eligibility decision made using information available at decision time."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    instrument_id: str = Field(min_length=1)
    decision_time: datetime
    eligible: bool
    reasons: tuple[EligibilityReason, ...] = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    evidence_available_at: datetime | None = None

    @field_validator("decision_time", "evidence_available_at")
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("decision timestamps must be UTC-aware")
        return value

    @model_validator(mode="after")
    def validate_decision(self) -> "EligibilityDecision":
        future_evidence = (
            self.evidence_available_at is not None
            and self.evidence_available_at > self.decision_time
        )
        if future_evidence and self.reasons != (EligibilityReason.FUTURE_INFORMATION,):
            raise ValueError("future evidence requires the future_information reason")
        if self.eligible and self.reasons != (EligibilityReason.ELIGIBLE,):
            raise ValueError("an eligible decision must contain only the eligible reason")
        if not self.eligible and EligibilityReason.ELIGIBLE in self.reasons:
            raise ValueError("an ineligible decision cannot contain the eligible reason")
        return self
