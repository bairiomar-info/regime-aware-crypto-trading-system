"""Deterministic Parquet writing and canonical dataset publication."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from ..models import Candle
from .models import CanonicalDatasetManifest, CanonicalDatasetResource

DECIMAL_PRECISION = 38
DECIMAL_SCALE = 18
ROW_GROUP_SIZE = 100_000
COMPRESSION = "zstd"
COMPRESSION_LEVEL = 3

CANONICAL_SCHEMA = pa.schema([
    pa.field("exchange", pa.string(), nullable=False),
    pa.field("symbol", pa.string(), nullable=False),
    pa.field("base_asset", pa.string(), nullable=False),
    pa.field("quote_asset", pa.string(), nullable=False),
    pa.field("timeframe", pa.string(), nullable=False),
    pa.field("open_time", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("close_time", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("open", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("high", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("low", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("close", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("volume", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("quote_volume", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("trade_count", pa.int64(), nullable=False),
    pa.field("taker_buy_base_volume", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("taker_buy_quote_volume", pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE), nullable=False),
    pa.field("source", pa.string(), nullable=False),
    pa.field("is_closed", pa.bool_(), nullable=False),
])

_COLUMNS = [field.name for field in CANONICAL_SCHEMA]
_DECIMAL_FIELDS = {
    "open", "high", "low", "close", "volume", "quote_volume",
    "taker_buy_base_volume", "taker_buy_quote_volume",
}


@dataclass(frozen=True)
class ParquetWriteResult:
    """Physical identity and statistics of one written Parquet resource."""

    resource: CanonicalDatasetResource
    schema: pa.Schema


class ParquetWriteError(ValueError):
    """Raised when canonical data cannot be represented by the V1 Parquet schema."""


def candles_to_arrow(candles: Iterable[Candle]) -> pa.Table:
    """Convert validated canonical candles into the exact V1 Arrow schema."""
    rows = list(candles)
    columns: dict[str, list[object]] = {name: [] for name in _COLUMNS}

    for candle in rows:
        columns["exchange"].append(candle.instrument.exchange)
        columns["symbol"].append(candle.instrument.symbol)
        columns["base_asset"].append(candle.instrument.base_asset)
        columns["quote_asset"].append(candle.instrument.quote_asset)
        columns["timeframe"].append(candle.timeframe.value)
        columns["open_time"].append(_require_utc(candle.open_time))
        columns["close_time"].append(_require_utc(candle.close_time))
        columns["trade_count"].append(candle.trade_count)
        columns["source"].append(candle.source)
        columns["is_closed"].append(candle.is_closed)
        for field in _DECIMAL_FIELDS:
            value = getattr(candle, field)
            _validate_decimal128(value, field)
            columns[field].append(value)

    arrays = [pa.array(columns[field.name], type=field.type) for field in CANONICAL_SCHEMA]
    return pa.Table.from_arrays(arrays, schema=CANONICAL_SCHEMA)


def write_canonical_parquet(
    candles: Iterable[Candle],
    path: str | Path,
    *,
    row_group_size: int = ROW_GROUP_SIZE,
) -> ParquetWriteResult:
    """Write one canonical resource atomically and return its physical identity."""
    if row_group_size < 1:
        raise ValueError("row_group_size must be positive")

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    table = candles_to_arrow(candles)

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        pq.write_table(
            table,
            temporary,
            compression=COMPRESSION,
            compression_level=COMPRESSION_LEVEL,
            row_group_size=row_group_size,
            use_dictionary=False,
            write_statistics=True,
            version="2.6",
            data_page_version="1.0",
        )
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    timestamps = table.column("open_time").to_pylist()
    resource = CanonicalDatasetResource(
        path=str(target),
        sha256=_sha256_file(target),
        byte_size=target.stat().st_size,
        row_count=table.num_rows,
        min_timestamp=_require_utc(timestamps[0]) if timestamps else None,
        max_timestamp=_require_utc(timestamps[-1]) if timestamps else None,
    )
    return ParquetWriteResult(resource=resource, schema=table.schema)


def publish_canonical_dataset(
    manifest: CanonicalDatasetManifest,
    manifest_path: str | Path,
) -> Path:
    """Atomically publish an already-validated immutable dataset manifest."""
    target = Path(manifest_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest.model_dump_json(indent=2) + "\n"

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return target


def read_candles(path: str | Path) -> list[dict]:
    """Read canonical records while preserving Arrow decimal values."""
    return pq.read_table(path, columns=_COLUMNS).to_pylist()


def _validate_decimal128(value: Decimal, field_name: str) -> None:
    if value.as_tuple().exponent < -DECIMAL_SCALE:
        raise ParquetWriteError(
            f"{field_name} value {value} exceeds V1 decimal scale {DECIMAL_SCALE}"
        )
    try:
        pa.scalar(value, type=pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE))
    except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
        raise ParquetWriteError(
            f"{field_name} value {value} cannot be represented as decimal128(38, {DECIMAL_SCALE})"
        ) from exc


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ParquetWriteError("canonical timestamps must be UTC-aware")
    return value.astimezone(UTC)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
