"""Load canonical parquet rows and expose one research dataset boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .candle_conversion import rows_to_candles
from trading_system.data.models import Instrument, Timeframe


@dataclass(frozen=True)
class CandleDataset:
    """Validated tabular dataset boundary used by experiment orchestration."""

    rows: tuple[dict[str, Any], ...]
    source: str

    def to_candles(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
    ):
        return rows_to_candles(
            self.rows,
            instrument=instrument,
            timeframe=timeframe,
            source=self.source,
        )


def load_candle_dataset(path: str | Path) -> CandleDataset:
    """Load a parquet dataset without duplicating Candle construction logic."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError("pyarrow is required to load parquet research datasets") from exc

    rows = tuple(dict(row) for row in parquet.read_table(target).to_pylist())
    if not rows:
        raise ValueError("research dataset must not be empty")
    return CandleDataset(rows=rows, source=str(target))
