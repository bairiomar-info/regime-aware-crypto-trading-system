from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from ..models import Candle, Instrument, Timeframe
from ..storage.parquet import write_candles
from .manifest import AcquisitionManifest

_INTERVALS = {
    Timeframe.M1: timedelta(minutes=1), Timeframe.M5: timedelta(minutes=5),
    Timeframe.M15: timedelta(minutes=15), Timeframe.H1: timedelta(hours=1),
    Timeframe.H4: timedelta(hours=4), Timeframe.D1: timedelta(days=1),
}

class HistoricalCandleProvider(Protocol):
    def fetch(self, *, instrument: Instrument, timeframe: Timeframe, start: datetime, end: datetime) -> list[Candle]: ...

class AcquisitionDataQualityError(ValueError):
    pass

def acquire_to_parquet(*, provider: HistoricalCandleProvider, instrument: Instrument, timeframe: Timeframe,
                       start: datetime, end: datetime, destination: str | Path,
                       dataset_name: str = "spot_ohlcv", dataset_version: str = "1.0.0",
                       validation_version: str = "1.0.0") -> AcquisitionManifest:
    _validate_bounds(start, end)
    candles = provider.fetch(instrument=instrument, timeframe=timeframe, start=start, end=end)
    ordered, duplicates = _deduplicate(candles)
    gaps = _count_gaps(ordered, timeframe)
    if gaps:
        raise AcquisitionDataQualityError(f"historical dataset contains {gaps} interval gaps")
    closed = [c for c in ordered if c.is_closed]
    if not closed:
        raise AcquisitionDataQualityError("acquisition produced no closed candles")
    write_candles(destination, closed)
    return AcquisitionManifest(dataset_name=dataset_name, dataset_version=dataset_version,
        provider=instrument.exchange, symbol=instrument.symbol, timeframe=timeframe.value,
        requested_start=start, requested_end=end, persisted_start=closed[0].open_time,
        persisted_end=closed[-1].open_time, candle_count=len(closed),
        status="partial" if len(closed) != len(ordered) else "complete",
        duplicate_count=duplicates, gap_count=0, validation_version=validation_version)

def _deduplicate(candles: list[Candle]) -> tuple[list[Candle], int]:
    by_open: dict[datetime, Candle] = {}; duplicates = 0
    for candle in candles:
        if candle.open_time in by_open:
            duplicates += 1
            if by_open[candle.open_time].model_dump() != candle.model_dump():
                raise AcquisitionDataQualityError("conflicting duplicate candle detected")
        else:
            by_open[candle.open_time] = candle
    return sorted(by_open.values(), key=lambda c: c.open_time), duplicates

def _count_gaps(candles: list[Candle], timeframe: Timeframe) -> int:
    interval = _INTERVALS[timeframe]
    return sum(1 for a, b in zip(candles, candles[1:]) if b.open_time - a.open_time != interval)

def _validate_bounds(start: datetime, end: datetime) -> None:
    if start.tzinfo is None or start.utcoffset() is None or end.tzinfo is None or end.utcoffset() is None:
        raise ValueError("acquisition bounds must be timezone-aware")
    if end <= start:
        raise ValueError("acquisition end must be after start")
    if start.astimezone(timezone.utc) != start or end.astimezone(timezone.utc) != end:
        raise ValueError("acquisition bounds must use UTC")
