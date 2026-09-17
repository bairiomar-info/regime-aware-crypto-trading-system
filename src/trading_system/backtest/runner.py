"""Deterministic orchestration for causal strategy backtests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from decimal import Decimal

from trading_system.strategies.models import StrategySignal

from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .results import BacktestResult, EquityPoint, calculate_max_drawdown, calculate_total_return

SignalFactory = Callable[[MarketBar, Sequence[MarketBar]], StrategySignal]


def run_backtest(
    bars: Sequence[MarketBar],
    signal_factory: SignalFactory,
    config: BacktestConfig,
) -> BacktestResult:
    """Run a strategy causally: a signal from bar i can execute no earlier than bar i+1."""
    if len(bars) < 2:
        raise ValueError("at least two market bars are required")
    for previous, current in zip(bars, bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological")

    state = BacktestState(cash=config.initial_cash, quantity=Decimal("0"))
    equity_curve: list[EquityPoint] = [EquityPoint(bars[0].timestamp, config.initial_cash)]

    for index in range(len(bars) - 1):
        decision_bar = bars[index]
        execution_bar = bars[index + 1]
        signal = signal_factory(decision_bar, bars[: index + 1])
        if not isinstance(signal, StrategySignal):
            raise TypeError("signal_factory must return a StrategySignal")
        if signal.decision_time != decision_bar.timestamp:
            raise ValueError("signal decision_time must match the decision bar timestamp")
        state = execute_signal(state, signal, execution_bar, config)
        equity = state.cash + state.quantity * execution_bar.close
        equity_curve.append(EquityPoint(execution_bar.timestamp, equity))

    final_equity = equity_curve[-1].equity
    curve = tuple(equity_curve)
    return BacktestResult(
        initial_cash=config.initial_cash,
        final_cash=state.cash,
        final_quantity=state.quantity,
        final_equity=final_equity,
        total_return=calculate_total_return(config.initial_cash, final_equity),
        max_drawdown=calculate_max_drawdown(curve),
        equity_curve=curve,
    )
