"""End-to-end causal single-asset strategy backtest orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_system.strategies.interface import ResearchStrategy, evaluate_strategy
from trading_system.strategies.models import StrategyContext
from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .results import BacktestResult, EquityPoint


@dataclass(frozen=True)
class IntegratedBacktestInput:
    bars: tuple[MarketBar, ...]
    contexts: tuple[StrategyContext, ...]


def run_strategy_backtest(strategy: ResearchStrategy, data: IntegratedBacktestInput, config: BacktestConfig) -> BacktestResult:
    """Evaluate point-in-time contexts and execute resulting signals on the next bar."""
    if not data.bars:
        raise ValueError("bars must not be empty")
    for previous, current in zip(data.bars, data.bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological")
    if any(context.symbol != data.contexts[0].symbol for context in data.contexts) if data.contexts else False:
        raise ValueError("all contexts must target the same symbol")
    bar_times = {bar.timestamp for bar in data.bars}
    if len({context.decision_time for context in data.contexts}) != len(data.contexts):
        raise ValueError("contexts must have unique decision times")
    signals = tuple(evaluate_strategy(strategy, context) for context in data.contexts)
    if any(signal.decision_time not in bar_times for signal in signals):
        raise ValueError("every signal decision_time must correspond to a market bar")
    if any(signal.symbol != data.contexts[i].symbol for i, signal in enumerate(signals)):
        raise ValueError("strategy signal symbol must match its context")

    state = BacktestState(config.initial_cash, Decimal("0"))
    curve: list[EquityPoint] = []
    by_time = {signal.decision_time: signal for signal in signals}
    for index, bar in enumerate(data.bars):
        signal = by_time.get(bar.timestamp)
        if signal is not None:
            if index + 1 >= len(data.bars):
                raise ValueError("final-bar signal has no executable next bar")
            state = execute_signal(state, signal, data.bars[index + 1], config)
        curve.append(EquityPoint(bar.timestamp, state.cash + state.quantity * bar.close))

    peak = curve[0].equity
    max_dd = Decimal("0")
    for point in curve:
        peak = max(peak, point.equity)
        max_dd = min(max_dd, point.equity / peak - Decimal("1"))
    final = curve[-1].equity
    return BacktestResult(config.initial_cash, state.cash, state.quantity, final, final / config.initial_cash - Decimal("1"), max_dd, tuple(curve))
