from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import MarketBar
from trading_system.backtest.walk_forward import make_walk_forward_windows


def bars(n: int) -> tuple[MarketBar, ...]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(MarketBar(start + timedelta(hours=i), Decimal("100"), Decimal("101")) for i in range(n))


def test_walk_forward_windows_are_causal() -> None:
    windows = make_walk_forward_windows(bars(10), train_size=4, test_size=2)
    assert len(windows) == 3
    for window in windows:
        assert window.test[0].timestamp > window.train[-1].timestamp


def test_walk_forward_rejects_non_chronological_data() -> None:
    data = list(bars(5))
    data[2], data[3] = data[3], data[2]
    with pytest.raises(ValueError, match="strictly chronological"):
        make_walk_forward_windows(tuple(data), train_size=2, test_size=1)
