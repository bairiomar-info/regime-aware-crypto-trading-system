"""Convert canonical dataset rows into validated Candle models."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from trading_system.data.models import Candle, Instrument, Timeframe


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
            **row,
        )
        for row in rows
    )
    if not candles:
        raise ValueError("dataset must contain at least one candle")
    return candles
