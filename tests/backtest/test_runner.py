from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.runner import run_backtest
from trading_system.strategies.models import SignalDirection, StrategySignal


def bars() -> tuple[MarketBar, ...]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        MarketBar(start + timedelta(days=i), Decimal("100"), Decimal(str(value)))
        for i, value in enumerate((100, 110, 120))
    )


def signal_factory(bar: MarketBar, history: tuple[MarketBar, ...]) -> StrategySignal:
    return StrategySignal(
        decision_time=bar.timestamp,
        symbol="BTCUSDT",
        direction=SignalDirection.LONG if len(history) == 1 else SignalDirection.NO_TRADE,
        reason="test",
        target_weight=Decimal("1") if len(history) == 1 else None,
    )


def test_runner_executes_signal_on_next_bar() -> None:
    result = run_backtest(bars(), signal_factory, BacktestConfig(initial_cash=Decimal("100")))
    assert result.final_equity == Decimal("120")
    assert result.total_return == Decimal("0.2")


def test_runner_requires_two_bars() -> None:
    with pytest.raises(ValueError):
        run_backtest(bars()[:1], signal_factory, BacktestConfig(initial_cash=Decimal("100")))


def test_runner_rejects_non_chronological_bars() -> None:
    source = bars()
    invalid = (source[0], source[2], source[1])
    with pytest.raises(ValueError, match="strictly chronological"):
        run_backtest(invalid, signal_factory, BacktestConfig(initial_cash=Decimal("100")))


def test_runner_rejects_signal_with_mismatched_decision_time() -> None:
    source = bars()

    def invalid_factory(bar: MarketBar, history: tuple[MarketBar, ...]) -> StrategySignal:
        return StrategySignal(
            decision_time=source[2].timestamp,
            symbol="BTCUSDT",
            direction=SignalDirection.NO_TRADE,
            reason="invalid_future_decision",
        )

    with pytest.raises(ValueError, match="decision_time must match"):
        run_backtest(source, invalid_factory, BacktestConfig(initial_cash=Decimal("100")))


def test_runner_rejects_non_signal_factory_result() -> None:
    def invalid_factory(bar: MarketBar, history: tuple[MarketBar, ...]) -> object:
        return object()

    with pytest.raises(TypeError, match="StrategySignal"):
        run_backtest(bars(), invalid_factory, BacktestConfig(initial_cash=Decimal("100")))
