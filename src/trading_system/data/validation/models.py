"""Validation result and anomaly models."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnomalySeverity(StrEnum):
    """Severity assigned to a validation anomaly."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationStatus(StrEnum):
    """Overall status of a validation run."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class ValidationAnomaly(BaseModel):
    """A structured, traceable data-quality anomaly."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1)
    severity: AnomalySeverity
    message: str = Field(min_length=1)
    index: int | None = Field(default=None, ge=0)
    context: dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    """Summary of a record or sequence validation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: ValidationStatus
    records_checked: int = Field(ge=0)
    valid_records: int = Field(ge=0)
    invalid_records: int = Field(ge=0)
    duplicate_count: int = Field(default=0, ge=0)
    gap_count: int = Field(default=0, ge=0)
    out_of_order_count: int = Field(default=0, ge=0)
    anomalies: tuple[ValidationAnomaly, ...] = ()
