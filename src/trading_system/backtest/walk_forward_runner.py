"""Walk-forward out-of-sample execution with training history retained only as context."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .evaluation import OOSSummary, OOSWindowResult, summarize_oos
from .results import BacktestResult, EquityPoint, calculate_max_drawdown, calculate_total_return
from .runner import SignalFactory
from .walk_forward import make_walk_forward_windows


def run_walk_forward_oos(
    bars: Sequence[MarketBar],
    signal_factory: SignalFactory,
    config: BacktestConfig,
    *,
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> OOSSummary:
    """Execute rolling test windows causally while retaining train history for signals."""
    windows = make_walk_forward_windows(tuple(bars), train_size=train_size, test_size=test_size, step=step)
    if not windows:
        raise ValueError("dataset does not contain a complete train/test window")

    results: list[OOSWindowResult] = []
    for index, window in enumerate(windows):
        result = _run_window(window.train, window.test, signal_factory, config)
        results.append(OOSWindowResult(index, result.total_return, result.max_drawdown))
    return summarize_oos(tuple(results))


def _run_window(
    train: Sequence[MarketBar],
    test: Sequence[MarketBar],
    signal_factory: SignalFactory,
    config: BacktestConfig,
) -> BacktestResult:
    if not train or not test:
        raise ValueError("train and test must not be empty")
    if any(current.timestamp <= previous.timestamp for previous, current in zip(test, test[1:])):
        raise ValueError("test bars must be strictly chronological")

    all_bars = tuple(train) + tuple(test)
    boundary = len(train)
    state = BacktestState(cash=config.initial_cash, quantity=Decimal("0"))
    curve: list[EquityPoint] = [EquityPoint(test[0].timestamp, config.initial_cash)]

    for index in range(boundary - 1, len(all_bars) - 1):
        decision_bar = all_bars[index]
        execution_bar = all_bars[index + 1]
        signal = signal_factory(decision_bar, all_bars[: index + 1])
        state = execute_signal(state, signal, execution_bar, config)
        if index + 1 >= boundary:
            equity = state.cash + state.quantity * execution_bar.close
            curve.append(EquityPoint(execution_bar.timestamp, equity))

    final = curve[-1].equity
    return BacktestResult(
        initial_cash=config.initial_cash,
        final_cash=state.cash,
        final_quantity=state.quantity,
        final_equity=final,
        total_return=calculate_total_return(config.initial_cash, final),
        max_drawdown=calculate_max_drawdown(tuple(curve)),
        equity_curve=tuple(curve),
    )
