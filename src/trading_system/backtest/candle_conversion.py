"""Convert canonical dataset rows into validated Candle models."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timezone
from typing import Any

from trading_system.data.models import Candle, Instrument, Timeframe


def _normalize_utc(value: Any) -> Any:
    """Normalize timezone-aware datetimes to the canonical UTC tzinfo object."""
    if hasattr(value, "tzinfo") and value.tzinfo is not None and value.utcoffset() is not None:
        return value.astimezone(timezone.utc)
    return value


def rows_to_candles(
    rows: Iterable[dict[str, Any]],
    *,
    instrument: Instrument,
    timeframe: Timeframe,
    source: str,
) -> tuple[Candle, ...]:
    """Validate dataset rows at the research boundary."""
    candles = tuple(
        Candle(
            instrument=instrument,
            timeframe=timeframe,
            source=source,
            **{
                **row,
                "open_time": _normalize_utc(row["open_time"]),
                "close_time": _normalize_utc(row["close_time"]),
            },
        )
        for row in rows
    )
    if not candles:
        raise ValueError("dataset must contain at least one candle")
    return candles
