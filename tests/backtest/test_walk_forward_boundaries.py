from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import MarketBar
from trading_system.backtest.walk_forward import WalkForwardWindow, make_walk_forward_windows


def _bars(count: int) -> tuple[MarketBar, ...]:
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    return tuple(
        MarketBar(
            timestamp=start + timedelta(hours=i),
            open=Decimal(100 + i),
            close=Decimal(100 + i),
        )
        for i in range(count)
    )


def test_rolling_windows_have_strict_temporal_boundaries() -> None:
    windows = make_walk_forward_windows(_bars(10), train_size=4, test_size=2)
    assert len(windows) == 3
    assert windows[0].train[-1].timestamp < windows[0].test[0].timestamp
    assert windows[1].train[-1].timestamp < windows[1].test[0].timestamp
    assert windows[2].train[-1].timestamp < windows[2].test[0].timestamp


def test_step_can_create_rolling_overlapping_training_histories() -> None:
    windows = make_walk_forward_windows(_bars(10), train_size=4, test_size=2, step=1)
    assert len(windows) == 5
    assert windows[0].test[0].timestamp < windows[1].test[0].timestamp
    assert windows[0].train[1].timestamp == windows[1].train[0].timestamp


def test_invalid_window_parameters_are_rejected() -> None:
    bars = _bars(6)
    with pytest.raises(ValueError, match="positive"):
        make_walk_forward_windows(bars, train_size=0, test_size=2)
    with pytest.raises(ValueError, match="positive"):
        make_walk_forward_windows(bars, train_size=2, test_size=2, step=0)


def test_empty_train_or_test_is_rejected() -> None:
    bars = _bars(2)
    with pytest.raises(ValueError, match="must not be empty"):
        WalkForwardWindow(train=(), test=bars)
    with pytest.raises(ValueError, match="must not be empty"):
        WalkForwardWindow(train=bars, test=())
