"""Immutable research-dataset publication metadata."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ResearchDatasetManifest(BaseModel):
    """Manifest describing one reproducible point-in-time research snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    research_dataset_id: str = Field(min_length=1)
    research_dataset_version: str = Field(
        pattern=r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
    )
    canonical_dataset_id: str = Field(min_length=1)
    canonical_dataset_version: str = Field(min_length=1)
    universe_policy_id: str = Field(min_length=1)
    universe_policy_version: str = Field(min_length=1)
    start_time: datetime
    end_time: datetime
    decision_frequency: str = Field(min_length=1)
    code_commit: str | None = None
    configuration_hash: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    membership_count: int = Field(ge=0)

    @field_validator("start_time", "end_time")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("research dataset bounds must be UTC-aware")
        return value

    @model_validator(mode="after")
    def validate_bounds(self) -> "ResearchDatasetManifest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self
