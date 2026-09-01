from datetime import UTC, datetime

import pytest

from trading_system.data.storage import DatasetIdentity, Provenance, StorageRecord


@pytest.fixture
def provenance() -> Provenance:
    return Provenance(
        provider="binance",
        source_type="rest",
        acquired_at=datetime(2026, 9, 1, tzinfo=UTC),
        normalization_version="1.0.0",
        validation_version="1.0.0",
        schema_version="1.0.0",
        source_request="GET /api/v3/klines",
    )


def test_storage_record_requires_utc_open_time():
    with pytest.raises(ValueError):
        StorageRecord(
            provider="binance",
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=datetime(2026, 9, 1),
        )


def test_storage_record_normalizes_identity():
    record = StorageRecord(
        provider="Binance",
        symbol="btcusdt",
        timeframe="1H",
        open_time=datetime(2026, 9, 1, tzinfo=UTC),
    )
    assert record.provider == "BINANCE"
    assert record.symbol == "BTCUSDT"
    assert record.timeframe == "1H"


def test_provenance_requires_utc_acquisition_time():
    with pytest.raises(ValueError):
        Provenance(
            provider="binance",
            source_type="rest",
            acquired_at=datetime(2026, 9, 1),
            normalization_version="1.0.0",
            validation_version="1.0.0",
            schema_version="1.0.0",
        )


def test_dataset_identity_is_reproducible_metadata(provenance):
    dataset = DatasetIdentity(
        dataset_name="spot_ohlcv",
        dataset_version="2026.09.01",
        symbol="BTCUSDT",
        timeframe="1h",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
        provenance=provenance,
    )
    assert dataset.provenance.normalization_version == "1.0.0"


def test_dataset_identity_rejects_reversed_bounds(provenance):
    with pytest.raises(ValueError):
        DatasetIdentity(
            dataset_name="spot_ohlcv",
            dataset_version="2026.09.01",
            symbol="BTCUSDT",
            timeframe="1h",
            start=datetime(2026, 1, 2, tzinfo=UTC),
            end=datetime(2026, 1, 1, tzinfo=UTC),
            provenance=provenance,
        )
