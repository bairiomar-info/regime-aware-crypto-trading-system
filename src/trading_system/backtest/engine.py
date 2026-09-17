"""Causal long-only spot backtest primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.research.time import require_utc
from trading_system.strategies.models import SignalDirection, StrategySignal


@dataclass(frozen=True)
class MarketBar:
    timestamp: datetime
    open: Decimal
    close: Decimal

    def __post_init__(self) -> None:
        require_utc(self.timestamp, name="bar timestamp")
        for name, value in (("open", self.open), ("close", self.close)):
            if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
                raise ValueError(f"{name} must be a positive finite Decimal")


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: Decimal
    fee_rate: Decimal = Decimal("0")
    slippage_rate: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        for name, value in (("initial_cash", self.initial_cash), ("fee_rate", self.fee_rate), ("slippage_rate", self.slippage_rate)):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError(f"{name} must be a finite Decimal")
        if self.initial_cash <= 0 or self.fee_rate < 0 or self.slippage_rate < 0:
            raise ValueError("initial_cash must be positive and rates non-negative")
        if self.fee_rate >= 1 or self.slippage_rate >= 1:
            raise ValueError("fee_rate and slippage_rate must be below 1")


@dataclass(frozen=True)
class BacktestState:
    cash: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        if not self.cash.is_finite() or not self.quantity.is_finite() or self.cash < 0 or self.quantity < 0:
            raise ValueError("spot state cannot contain negative or non-finite balances")


def execute_signal(state: BacktestState, signal: StrategySignal, execution_bar: MarketBar, config: BacktestConfig) -> BacktestState:
    """Apply a target-weight signal at a later bar using deterministic execution prices."""
    if execution_bar.timestamp <= signal.decision_time:
        raise ValueError("execution must occur strictly after signal decision_time")
    if signal.direction is SignalDirection.NO_TRADE:
        return state
    if signal.direction is not SignalDirection.LONG:
        raise ValueError("only LONG and NO_TRADE are supported")
    if signal.target_weight is None:
        raise ValueError("LONG signal requires target_weight")

    buy_price = execution_bar.open * (Decimal("1") + config.slippage_rate)
    sell_price = execution_bar.open * (Decimal("1") - config.slippage_rate)
    current_equity = state.cash + state.quantity * sell_price
    target_value = current_equity * signal.target_weight
    target_quantity = target_value / buy_price
    delta = target_quantity - state.quantity

    if delta > 0:
        affordable = min(delta, state.cash / (buy_price * (Decimal("1") + config.fee_rate)))
        gross = affordable * buy_price
        fee = gross * config.fee_rate
        remaining_cash = max(Decimal("0"), state.cash - gross - fee)
        return BacktestState(remaining_cash, state.quantity + affordable)
    if delta < 0:
        sold = min(-delta, state.quantity)
        gross = sold * sell_price
        fee = gross * config.fee_rate
        return BacktestState(state.cash + gross - fee, state.quantity - sold)
    return state
