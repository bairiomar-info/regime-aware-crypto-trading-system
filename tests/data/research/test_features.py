from decimal import Decimal

import pytest

from trading_system.data.research.features import ema, ema_trend_score, rolling_volatility, simple_return


def test_simple_return_uses_only_requested_historical_window():
    result = simple_return(["100", "110", "121", "133.1"], lookback_bars=2)
    assert result == Decimal("0.1")


def test_simple_return_requires_anchor_history():
    assert simple_return(["100", "110"], lookback_bars=2) is None


def test_simple_return_rejects_non_positive_prices():
    with pytest.raises(ValueError, match="positive"):
        simple_return(["100", "0", "110"], lookback_bars=1)


def test_rolling_volatility_is_zero_for_constant_returns():
    result = rolling_volatility(["100", "110", "121", "133.1"], lookback_bars=3)
    assert result == Decimal("0")


def test_rolling_volatility_is_parameterized_by_annualization_factor():
    daily = rolling_volatility(["100", "101", "100", "101"], lookback_bars=3)
    annualized = rolling_volatility(
        ["100", "101", "100", "101"],
        lookback_bars=3,
        annualization_factor="4",
    )
    assert annualized == daily * Decimal("2")


def test_rolling_volatility_requires_history():
    assert rolling_volatility(["100", "101"], lookback_bars=3) is None


def test_ema_requires_span_history():
    assert ema(["100", "110"], span=3) is None


def test_ema_starts_from_simple_average_of_initial_span():
    result = ema(["100", "110", "120"], span=3)
    assert result == Decimal("110")


def test_ema_trend_score_is_positive_when_fast_ema_is_above_slow_ema():
    result = ema_trend_score(["100", "100", "100", "110", "120"], fast_span=2, slow_span=4)
    assert result is not None
    assert result > 0


def test_ema_trend_score_requires_distinct_fast_and_slow_spans():
    with pytest.raises(ValueError, match="smaller"):
        ema_trend_score(["100", "101", "102", "103"], fast_span=4, slow_span=4)


def test_ema_trend_score_requires_slow_history():
    assert ema_trend_score(["100", "101", "102"], fast_span=2, slow_span=4) is None
