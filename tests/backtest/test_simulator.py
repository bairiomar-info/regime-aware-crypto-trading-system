from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.simulator import run_backtest
from trading_system.strategies.models import SignalDirection, StrategySignal


def bar(hour: int, price: str) -> MarketBar:
    return MarketBar(datetime(2026, 1, 1, hour, tzinfo=timezone.utc), Decimal(price), Decimal(price))


def signal(hour: int, direction=SignalDirection.LONG) -> StrategySignal:
    return StrategySignal(
        datetime(2026, 1, 1, hour, tzinfo=timezone.utc),
        "BTCUSDT",
        direction,
        "test",
        target_weight=Decimal("1") if direction is SignalDirection.LONG else None,
    )


def test_execution_uses_next_bar_and_tracks_equity() -> None:
    result = run_backtest(
        tuple(bar(i, str(100 + i * 10)) for i in range(3)),
        (signal(0),),
        BacktestConfig(Decimal("1000")),
    )
    assert result.final_equity == Decimal("1100")
    assert result.total_return == Decimal("0.1")


def test_final_bar_signal_is_rejected() -> None:
    with pytest.raises(ValueError, match="final bar"):
        run_backtest((bar(0, "100"), bar(1, "110")), (signal(1),), BacktestConfig(Decimal("1000")))


def test_bars_must_be_chronological() -> None:
    with pytest.raises(ValueError, match="chronological"):
        run_backtest((bar(1, "100"), bar(0, "110")), (), BacktestConfig(Decimal("1000")))


def test_no_trade_does_not_change_cash() -> None:
    result = run_backtest(
        (bar(0, "100"), bar(1, "120")),
        (signal(0, SignalDirection.NO_TRADE),),
        BacktestConfig(Decimal("1000")),
    )
    assert result.final_cash == Decimal("1000")
    assert result.final_quantity == Decimal("0")
