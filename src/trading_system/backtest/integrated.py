"""End-to-end causal single-asset strategy backtest orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.strategies.interface import ResearchStrategy, evaluate_strategy
from trading_system.strategies.models import StrategyContext, StrategySignal
from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .results import BacktestResult, EquityPoint


@dataclass(frozen=True)
class IntegratedBacktestInput:
    bars: tuple[MarketBar, ...]
    contexts: tuple[StrategyContext, ...]


def run_strategy_backtest(
    strategy: ResearchStrategy,
    data: IntegratedBacktestInput,
    config: BacktestConfig,
) -> BacktestResult:
    """Evaluate a strategy at each supplied context and execute only on a later bar."""
    if not data.bars:
        raise ValueError("bars must not be empty")
    for previous, current in zip(data.bars, data.bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly chronological")
    signals: list[StrategySignal] = []
    for context in data.contexts:
        signals.append(evaluate_strategy(strategy, context))
    if any(signal.decision_time not in {bar.timestamp for bar in data.bars} for signal in signals):
        raise ValueError("every signal decision_time must correspond to a market bar")

    state = BacktestState(config.initial_cash, Decimal("0"))
    curve: list[EquityPoint] = []
    by_time = {signal.decision_time: signal for signal in signals}
    for index, bar in enumerate(data.bars):
        signal = by_time.get(bar.timestamp)
        if signal is not None:
            if index + 1 >= len(data.bars):
                raise ValueError("final-bar signal has no executable next bar")
            state = execute_signal(state, signal, data.bars[index + 1], config)
        equity = state.cash + state.quantity * bar.close
        curve.append(EquityPoint(bar.timestamp, equity))

    final_equity = curve[-1].equity
    peak = curve[0].equity
    drawdown = Decimal("0")
    for point in curve:
        peak = max(peak, point.equity)
        drawdown = min(drawdown, point.equity / peak - Decimal("1"))
    return BacktestResult(
        config.initial_cash,
        state.cash,
        state.quantity,
        final_equity,
        final_equity / config.initial_cash - Decimal("1"),
        drawdown,
        tuple(curve),
    )
