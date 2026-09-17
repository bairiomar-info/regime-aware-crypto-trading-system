"""Chronological single-asset spot backtest simulator."""

from __future__ import annotations

from decimal import Decimal

from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .results import BacktestResult, EquityPoint
from trading_system.strategies.models import StrategySignal


def run_backtest(
    bars: tuple[MarketBar, ...],
    signals: tuple[StrategySignal, ...],
    config: BacktestConfig,
) -> BacktestResult:
    """Replay signals against strictly later bars using deterministic fills.

    A signal decided at bar ``t`` is queued and executed at bar ``t+1`` before
    that bar is marked to market. This preserves causal timing while ensuring
    the equity curve reflects fills at the bar on which they actually occur.
    """
    if not bars:
        raise ValueError("bars must not be empty")
    if len(signals) > len(bars):
        raise ValueError("signals cannot exceed bar count")
    for previous, current in zip(bars, bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological")
    for prev_signal, next_signal in zip(signals, signals[1:]):
        if next_signal.decision_time <= prev_signal.decision_time:
            raise ValueError("signals must be strictly chronological")

    state = BacktestState(cash=config.initial_cash, quantity=Decimal("0"))
    curve: list[EquityPoint] = []
    signal_by_time = {signal.decision_time: signal for signal in signals}
    pending: StrategySignal | None = None

    for index, bar in enumerate(bars):
        if pending is not None:
            state = execute_signal(state, pending, bar, config)

        equity = state.cash + state.quantity * bar.close
        curve.append(EquityPoint(timestamp=bar.timestamp, equity=equity))

        signal = signal_by_time.get(bar.timestamp)
        if signal is not None:
            if index + 1 >= len(bars):
                raise ValueError("a signal on the final bar has no later execution bar")
            pending = signal
        else:
            pending = None

    initial = config.initial_cash
    final = curve[-1].equity
    peak = curve[0].equity
    max_drawdown = Decimal("0")
    for point in curve:
        if point.equity > peak:
            peak = point.equity
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - point.equity) / peak)

    return BacktestResult(
        initial_cash=initial,
        final_cash=state.cash,
        final_quantity=state.quantity,
        final_equity=final,
        total_return=(final / initial) - Decimal("1"),
        max_drawdown=max_drawdown,
        equity_curve=tuple(curve),
    )
