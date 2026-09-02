"""Contracts and deterministic transformation for canonical market data."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..models import Candle


class QualityClassification(StrEnum):
    """Classification of an interval/observation after canonicalization."""

    VALID = "valid"
    NO_TRADES = "no_trades"
    DATA_GAP = "data_gap"
    SOURCE_FAILURE = "source_failure"
    HALT = "halt"
    BREAK = "break"
    UNKNOWN_GAP = "unknown_gap"
    DUPLICATE = "duplicate"
    DATA_CONFLICT = "data_conflict"


class CanonicalizationContract(BaseModel):
    """Immutable versioned contract governing raw-to-canonical transformation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    normalization_version: str = Field(min_length=1)
    validation_version: str = Field(min_length=1)
    require_closed_candles: bool = True
    numeric_representation: str = Field(default="decimal128", min_length=1)
    timestamp_timezone: str = Field(default="UTC", min_length=1)
    fabricate_missing_candles: bool = False
    reject_conflicting_duplicates: bool = True

    @field_validator("timestamp_timezone")
    @classmethod
    def require_utc(cls, value: str) -> str:
        if value.upper() != "UTC":
            raise ValueError("canonical timestamps must use UTC")
        return "UTC"

    @model_validator(mode="after")
    def validate_invariants(self) -> "CanonicalizationContract":
        if self.fabricate_missing_candles:
            raise ValueError("canonicalization must not fabricate missing candles")
        if self.numeric_representation.lower() != "decimal128":
            raise ValueError("V1 canonical numeric representation must be decimal128")
        return self


class QualityDiagnostic(BaseModel):
    """Immutable diagnostic explaining a canonical data-quality classification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    classification: QualityClassification
    observed_at: datetime
    message: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)

    @field_validator("observed_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("observed_at must be UTC-aware")
        return value


class CanonicalizationError(ValueError):
    """Raised when canonicalization encounters a non-recoverable conflict."""


@dataclass(frozen=True)
class CanonicalizationResult:
    """Deterministic result of canonicalizing normalized candles."""

    candles: tuple[Candle, ...]
    diagnostics: tuple[QualityDiagnostic, ...]


def canonicalize_candles(
    candles: Iterable[Candle],
    *,
    contract: CanonicalizationContract,
) -> CanonicalizationResult:
    """Canonicalize already-normalized candles without fabricating market data.

    The operation is pure: input objects are not mutated and output ordering is
    deterministic. Missing intervals are diagnosed as DATA_GAP because OHLCV
    alone cannot prove whether the cause was no trades, source failure, halt,
    or another condition.
    """

    ordered = sorted(
        candles,
        key=lambda candle: (
            candle.instrument.exchange,
            candle.instrument.symbol,
            candle.timeframe.value,
            candle.open_time,
        ),
    )

    diagnostics: list[QualityDiagnostic] = []
    unique: dict[tuple[str, str, str, datetime], Candle] = {}

    for candle in ordered:
        key = (
            candle.instrument.exchange,
            candle.instrument.symbol,
            candle.timeframe.value,
            candle.open_time,
        )

        if contract.require_closed_candles and not candle.is_closed:
            diagnostics.append(
                QualityDiagnostic(
                    classification=QualityClassification.UNKNOWN_GAP,
                    observed_at=candle.open_time,
                    message="incomplete candle excluded from canonical dataset",
                    symbol=candle.instrument.symbol,
                    timeframe=candle.timeframe.value,
                )
            )
            continue

        existing = unique.get(key)
        if existing is None:
            unique[key] = candle
            continue

        if existing == candle:
            diagnostics.append(
                QualityDiagnostic(
                    classification=QualityClassification.DUPLICATE,
                    observed_at=candle.open_time,
                    message="identical duplicate candle removed deterministically",
                    symbol=candle.instrument.symbol,
                    timeframe=candle.timeframe.value,
                )
            )
            continue

        diagnostics.append(
            QualityDiagnostic(
                classification=QualityClassification.DATA_CONFLICT,
                observed_at=candle.open_time,
                message="conflicting candles share the same canonical key",
                symbol=candle.instrument.symbol,
                timeframe=candle.timeframe.value,
            )
        )
        if contract.reject_conflicting_duplicates:
            raise CanonicalizationError(
                "conflicting candles share the same exchange/symbol/timeframe/open_time"
            )

    canonical = sorted(
        unique.values(),
        key=lambda candle: (
            candle.instrument.exchange,
            candle.instrument.symbol,
            candle.timeframe.value,
            candle.open_time,
        ),
    )

    by_series: dict[tuple[str, str, str], list[Candle]] = {}
    for candle in canonical:
        series_key = (
            candle.instrument.exchange,
            candle.instrument.symbol,
            candle.timeframe.value,
        )
        by_series.setdefault(series_key, []).append(candle)

    for series in by_series.values():
        expected = _timeframe_delta(series[0])
        for previous, current in zip(series, series[1:]):
            delta = current.open_time - previous.open_time
            if delta > expected:
                diagnostics.append(
                    QualityDiagnostic(
                        classification=QualityClassification.DATA_GAP,
                        observed_at=previous.open_time + expected,
                        message=(
                            f"missing interval(s) between {previous.open_time.isoformat()} "
                            f"and {current.open_time.isoformat()}"
                        ),
                        symbol=current.instrument.symbol,
                        timeframe=current.timeframe.value,
                    )
                )

    return CanonicalizationResult(
        candles=tuple(canonical),
        diagnostics=tuple(
            sorted(
                diagnostics,
                key=lambda diagnostic: (
                    diagnostic.symbol,
                    diagnostic.timeframe,
                    diagnostic.observed_at,
                    diagnostic.classification.value,
                ),
            )
        ),
    )


def _timeframe_delta(candle: Candle):
    """Return the expected open-time spacing for the supported V1 timeframe."""

    from datetime import timedelta

    deltas = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }
    return deltas[candle.timeframe.value]
