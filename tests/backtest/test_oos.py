from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import MarketBar
from trading_system.backtest.oos import WalkForwardWindow, run_oos


def _bar(day: int) -> MarketBar:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=day)
    return MarketBar(start, Decimal("100"), Decimal(str(100 + day)))


def test_oos_runner_rejects_overlapping_test_windows() -> None:
    bars = tuple(_bar(i) for i in range(8))
    windows = (
        WalkForwardWindow(train=bars[:2], test=bars[2:5]),
        WalkForwardWindow(train=bars[1:3], test=bars[4:7]),
    )
    with pytest.raises(ValueError, match="overlap"):
        run_oos(windows, lambda train, test: Decimal("0"))
