"""Parquet persistence for canonical market data."""

from pathlib import Path
from typing import Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from ..models import Candle


_COLUMNS = [
    "symbol", "timeframe", "open_time", "close_time", "open", "high", "low", "close",
    "volume", "quote_volume", "trade_count", "taker_buy_base_volume", "taker_buy_quote_volume",
    "source", "is_closed",
]


def _table(candles: Iterable[Candle]) -> pa.Table:
    rows = []
    for candle in candles:
        rows.append({
            "symbol": candle.instrument.symbol,
            "timeframe": str(candle.timeframe),
            "open_time": candle.open_time,
            "close_time": candle.close_time,
            "open": str(candle.open), "high": str(candle.high), "low": str(candle.low), "close": str(candle.close),
            "volume": str(candle.volume), "quote_volume": str(candle.quote_volume),
            "trade_count": candle.trade_count,
            "taker_buy_base_volume": str(candle.taker_buy_base_volume),
            "taker_buy_quote_volume": str(candle.taker_buy_quote_volume),
            "source": candle.source, "is_closed": candle.is_closed,
        })
    return pa.Table.from_pylist(rows, schema=pa.schema([
        pa.field("symbol", pa.string()), pa.field("timeframe", pa.string()),
        pa.field("open_time", pa.timestamp("us", tz="UTC")), pa.field("close_time", pa.timestamp("us", tz="UTC")),
        pa.field("open", pa.string()), pa.field("high", pa.string()), pa.field("low", pa.string()), pa.field("close", pa.string()),
        pa.field("volume", pa.string()), pa.field("quote_volume", pa.string()), pa.field("trade_count", pa.int64()),
        pa.field("taker_buy_base_volume", pa.string()), pa.field("taker_buy_quote_volume", pa.string()),
        pa.field("source", pa.string()), pa.field("is_closed", pa.bool_()),
    ]))


def write_candles(path: str | Path, candles: Iterable[Candle]) -> None:
    """Atomically write canonical candles to a Parquet file."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    table = _table(candles)
    pq.write_table(table, temporary, compression="zstd")
    temporary.replace(destination)


def read_candles(path: str | Path) -> list[dict]:
    """Read stored records without silently coercing financial strings to floats."""
    table = pq.read_table(path, columns=_COLUMNS)
    return table.to_pylist()
