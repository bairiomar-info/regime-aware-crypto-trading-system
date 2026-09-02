from datetime import UTC, datetime
from decimal import Decimal

import pytest

from trading_system.data.research.liquidity import rolling_quote_volume
from trading_system.data.research.readiness import ReadinessState, assess_readiness

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def test_readiness_requires_feature_history():
    result = assess_readiness(
        instrument_id="BINANCE:BTCUSDT",
        decision_time=T0,
        available_bars=19,
        required_bars=20,
    )
    assert result.state == ReadinessState.INSUFFICIENT_HISTORY


def test_readiness_can_be_feature_ready_without_universal_asset_age():
    result = assess_readiness(
        instrument_id="BINANCE:BTCUSDT",
        decision_time=T0,
        available_bars=20,
        required_bars=20,
    )
    assert result.state == ReadinessState.READY_FOR_FEATURES


def test_strategy_readiness_is_explicit():
    result = assess_readiness(
        instrument_id="BINANCE:BTCUSDT",
        decision_time=T0,
        available_bars=100,
        required_bars=20,
        strategy_ready=True,
    )
    assert result.state == ReadinessState.READY_FOR_STRATEGY


def test_readiness_requires_utc_decision_time():
    with pytest.raises(ValueError, match="UTC-aware"):
        assess_readiness(
            instrument_id="BINANCE:BTCUSDT",
            decision_time=datetime(2026, 1, 1),
            available_bars=20,
            required_bars=20,
        )


def test_rolling_quote_volume_uses_median():
    typical, coverage, sufficient = rolling_quote_volume(
        ["100", "110", "10000"],
        lookback_bars=3,
        minimum_quote_volume="100",
    )
    assert typical == Decimal("110")
    assert coverage == Decimal("1")
    assert sufficient is True


def test_liquidity_fails_when_coverage_is_insufficient():
    typical, coverage, sufficient = rolling_quote_volume(
        ["100", None],
        lookback_bars=3,
        minimum_coverage=Decimal("0.8"),
    )
    assert typical is None
    assert coverage == Decimal("0.3333333333333333333333333333")
    assert sufficient is False


def test_liquidity_threshold_is_configurable():
    _, _, sufficient = rolling_quote_volume(
        ["100", "110", "120"],
        lookback_bars=3,
        minimum_quote_volume="111",
    )
    assert sufficient is False


def test_liquidity_rejects_negative_volume():
    with pytest.raises(ValueError, match="cannot be negative"):
        rolling_quote_volume(["100", "-1"], lookback_bars=2)


def test_liquidity_rejects_invalid_volume():
    with pytest.raises(ValueError, match="valid decimal"):
        rolling_quote_volume(["100", "not-a-number"], lookback_bars=2)
