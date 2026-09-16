from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from trading_system.strategies.models import SignalDirection, StrategySignal


def test_buy_never_creates_negative_cash() -> None:
    bar = MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
    signal = StrategySignal("BTCUSDT", bar.timestamp.replace(hour=0), SignalDirection.LONG, Decimal("1"), Decimal("1"), "test")
    result = execute_signal(BacktestState(Decimal("10"), Decimal("0")), signal, bar, BacktestConfig(Decimal("10"), Decimal("0.01")))
    assert result.cash >= 0


def test_execution_must_be_after_decision() -> None:
    timestamp = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
    bar = MarketBar(timestamp, Decimal("100"), Decimal("100"))
    signal = StrategySignal("BTCUSDT", timestamp, SignalDirection.LONG, Decimal("1"), Decimal("1"), "test")
    with pytest.raises(ValueError, match="strictly after"):
        execute_signal(BacktestState(Decimal("100"), Decimal("0")), signal, bar, BacktestConfig(Decimal("100")))
