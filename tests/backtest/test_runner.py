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
    assert tuple(point.timestamp for point in result.equity_curve) == tuple(bar.timestamp for bar in bars())


def test_runner_requires_two_bars() -> None:
    with pytest.raises(ValueError):
        run_backtest(bars()[:1], signal_factory, BacktestConfig(initial_cash=Decimal("100")))


def test_runner_rejects_non_chronological_bars() -> None:
    source = bars()
    invalid = (source[0], source[2], source[1])
    with pytest.raises(ValueError, match="strictly chronological"):
        run_backtest(invalid, signal_factory, BacktestConfig(initial_cash=Decimal("100")))


def test_runner_rejects_duplicate_timestamps() -> None:
    source = bars()
    invalid = (source[0], source[1], source[1])
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


def test_runner_passes_only_past_and_current_bar_to_signal_factory() -> None:
    observed_lengths: list[int] = []

    def factory(bar: MarketBar, history: tuple[MarketBar, ...]) -> StrategySignal:
        observed_lengths.append(len(history))
        assert history[-1].timestamp == bar.timestamp
        assert all(item.timestamp <= bar.timestamp for item in history)
        return StrategySignal(bar.timestamp, "BTCUSDT", SignalDirection.NO_TRADE, "test")

    run_backtest(bars(), factory, BacktestConfig(initial_cash=Decimal("100")))
    assert observed_lengths == [1, 2]


def test_runner_is_deterministic_for_same_inputs() -> None:
    config = BacktestConfig(initial_cash=Decimal("100"), fee_rate=Decimal("0.001"), slippage_rate=Decimal("0.002"))
    first = run_backtest(bars(), signal_factory, config)
    second = run_backtest(bars(), signal_factory, config)
    assert first == second


def test_runner_propagates_signal_factory_failure_without_partial_result() -> None:
    calls = 0

    def failing_factory(bar: MarketBar, history: tuple[MarketBar, ...]) -> StrategySignal:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("strategy failure")
        return StrategySignal(bar.timestamp, "BTCUSDT", SignalDirection.NO_TRADE, "test")

    with pytest.raises(RuntimeError, match="strategy failure"):
        run_backtest(bars(), failing_factory, BacktestConfig(initial_cash=Decimal("100")))
