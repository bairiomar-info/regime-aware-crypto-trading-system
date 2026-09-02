from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pyarrow.parquet as pq
import pytest

from trading_system.data.models import Candle, Instrument, Timeframe
from trading_system.data.storage import (
    CANONICAL_SCHEMA,
    CanonicalDatasetManifest,
    CanonicalDatasetResource,
    ParquetWriteError,
    Provenance,
    candles_to_arrow,
    publish_canonical_dataset,
    read_candles,
    write_canonical_parquet,
)


def make_candle(minute: int, *, close: str = "101") -> Candle:
    start = datetime(2026, 1, 1, 0, minute, tzinfo=UTC)
    return Candle(
        instrument=Instrument(
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            exchange="BINANCE",
        ),
        timeframe=Timeframe.M1,
        open_time=start,
        close_time=start + timedelta(minutes=1) - timedelta(milliseconds=1),
        open=Decimal("100.123456789012345678"),
        high=Decimal("102.123456789012345678"),
        low=Decimal("99.123456789012345678"),
        close=Decimal(close),
        volume=Decimal("10.123456789012345678"),
        quote_volume=Decimal("1012.345678901234567890"),
        trade_count=10,
        taker_buy_base_volume=Decimal("5.123456789012345678"),
        taker_buy_quote_volume=Decimal("500.123456789012345678"),
        source="binance",
        is_closed=True,
    )


def test_arrow_schema_is_exact_and_decimal() -> None:
    table = candles_to_arrow([make_candle(0)])

    assert table.schema == CANONICAL_SCHEMA
    assert str(table.schema.field("open").type) == "decimal128(38, 18)"
    assert str(table.schema.field("open_time").type) == "timestamp[us, tz=UTC]"
    assert table.column("open")[0].as_py() == Decimal("100.123456789012345678")


def test_decimal_precision_beyond_frozen_scale_is_rejected() -> None:
    candle = make_candle(0)
    candle = candle.model_copy(update={"open": Decimal("1.1234567890123456789")})

    with pytest.raises(ParquetWriteError, match="decimal scale"):
        candles_to_arrow([candle])


def test_parquet_writer_is_atomic_and_records_physical_identity(tmp_path) -> None:
    path = tmp_path / "btc.parquet"
    result = write_canonical_parquet([make_candle(0), make_candle(1)], path)

    assert path.exists()
    assert result.resource.row_count == 2
    assert result.resource.byte_size == path.stat().st_size
    assert len(result.resource.sha256) == 64
    assert result.resource.min_timestamp == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    assert result.resource.max_timestamp == datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
    assert pq.read_schema(path) == CANONICAL_SCHEMA
    assert not list(tmp_path.glob("*.tmp"))


def test_parquet_round_trip_preserves_decimal_values(tmp_path) -> None:
    path = tmp_path / "btc.parquet"
    write_canonical_parquet([make_candle(0)], path)

    rows = read_candles(path)

    assert rows[0]["open"] == Decimal("100.123456789012345678")
    assert rows[0]["volume"] == Decimal("10.123456789012345678")


def test_same_canonical_input_has_stable_file_hash(tmp_path) -> None:
    first = tmp_path / "first.parquet"
    second = tmp_path / "second.parquet"
    candles = [make_candle(0), make_candle(1)]

    first_result = write_canonical_parquet(candles, first)
    second_result = write_canonical_parquet(candles, second)

    assert first_result.resource.sha256 == second_result.resource.sha256


def test_manifest_publication_is_atomic(tmp_path) -> None:
    parquet = tmp_path / "btc.parquet"
    resource = write_canonical_parquet([make_candle(0)], parquet).resource
    manifest = CanonicalDatasetManifest(
        dataset_id="spot_ohlcv",
        dataset_version="v1.0.0",
        schema_version="1.0.0",
        normalization_version="1.0.0",
        validation_version="1.0.0",
        input_artifact_ids=("sha256:" + "a" * 64,),
        code_commit="abc123",
        configuration_hash="b" * 64,
        resources=(resource,),
        total_row_count=1,
        min_timestamp=resource.min_timestamp,
        max_timestamp=resource.max_timestamp,
    )

    manifest_path = tmp_path / "manifest.json"
    published = publish_canonical_dataset(manifest, manifest_path)

    assert published == manifest_path
    assert manifest_path.exists()
    assert manifest_path.read_text(encoding="utf-8").endswith("\n")
    assert '"dataset_id": "spot_ohlcv"' in manifest_path.read_text(encoding="utf-8")


def test_empty_resource_has_no_timestamp_bounds(tmp_path) -> None:
    result = write_canonical_parquet([], tmp_path / "empty.parquet")

    assert result.resource.row_count == 0
    assert result.resource.min_timestamp is None
    assert result.resource.max_timestamp is None
