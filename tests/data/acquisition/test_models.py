from datetime import UTC, datetime, timedelta

import pytest

from trading_system.data.acquisition import (
    AcquisitionCheckpoint,
    AcquisitionChunk,
    AcquisitionRequest,
    AcquisitionResult,
    AcquisitionStatus,
    RetryPolicy,
)
from trading_system.data.models import Instrument, MarketType, Timeframe


@pytest.fixture
def request_model() -> AcquisitionRequest:
    return AcquisitionRequest(
        provider="binance",
        instrument=Instrument(base_asset="BTC", quote_asset="USDT", market_type=MarketType.SPOT),
        timeframe=Timeframe("1h"),
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )


def test_request_rejects_naive_bounds():
    with pytest.raises(ValueError):
        AcquisitionRequest(
            provider="binance",
            instrument=Instrument(base_asset="BTC", quote_asset="USDT", market_type=MarketType.SPOT),
            timeframe=Timeframe("1h"),
            start=datetime(2026, 1, 1),
            end=datetime(2026, 1, 2, tzinfo=UTC),
        )


def test_request_rejects_reversed_bounds(request_model):
    with pytest.raises(ValueError):
        request_model.model_copy(update={"end": request_model.start})


def test_checkpoint_accepts_successful_boundary(request_model):
    boundary = request_model.start + timedelta(hours=12)
    checkpoint = AcquisitionCheckpoint(
        request=request_model,
        last_successful_boundary=boundary,
        status=AcquisitionStatus.COMPLETED,
    )
    assert checkpoint.last_successful_boundary == boundary


def test_checkpoint_rejects_boundary_outside_request(request_model):
    with pytest.raises(ValueError):
        AcquisitionCheckpoint(
            request=request_model,
            last_successful_boundary=request_model.end + timedelta(hours=1),
        )


def test_chunk_requires_positive_interval():
    with pytest.raises(ValueError):
        AcquisitionChunk(start=datetime(2026, 1, 1, tzinfo=UTC), end=datetime(2026, 1, 1, tzinfo=UTC), sequence=0)


def test_result_tracks_persistence_and_validation(request_model):
    chunk = AcquisitionChunk(
        start=request_model.start,
        end=request_model.end,
        sequence=0,
    )
    result = AcquisitionResult(
        chunk=chunk,
        records_received=100,
        raw_persisted=True,
        validation_passed=True,
    )
    assert result.records_received == 100
    assert result.raw_persisted is True
    assert result.validation_passed is True


def test_retry_policy_exponential_backoff_is_capped():
    policy = RetryPolicy(max_attempts=5, initial_delay_seconds=2, max_delay_seconds=5, multiplier=2)
    assert policy.delay_seconds(1) == 2
    assert policy.delay_seconds(2) == 4
    assert policy.delay_seconds(3) == 5


def test_retry_policy_rejects_invalid_retry_number():
    with pytest.raises(ValueError):
        RetryPolicy().delay_seconds(0)
