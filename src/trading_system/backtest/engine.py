"""Causal long-only spot backtest primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.strategies.models import SignalDirection, StrategySignal
from trading_system.research.time import require_utc


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
        if self.cash < 0 or self.quantity < 0:
            raise ValueError("spot state cannot contain negative balances")


def execute_signal(
    state: BacktestState,
    signal: StrategySignal,
    execution_bar: MarketBar,
    config: BacktestConfig,
) -> BacktestState:
    """Apply one signal at the explicitly supplied execution bar.

    The caller is responsible for ensuring execution_bar.timestamp is strictly
    after the signal decision time. This function rejects same/future decision
    timing so a close cannot accidentally be used as its own fill.
    """
    if execution_bar.timestamp <= signal.decision_time:
        raise ValueError("execution must occur strictly after signal decision_time")

    if signal.direction is SignalDirection.NO_TRADE:
        return state

    if signal.direction is not SignalDirection.LONG:
        raise ValueError("only LONG and NO_TRADE are supported")

    price = execution_bar.open * (Decimal("1") + config.slippage_rate)
    target_value = config.initial_cash * signal.target_weight  # type: ignore[operator]
    desired_quantity = target_value / price
    additional = desired_quantity - state.quantity
    if additional <= 0:
        return state

    gross = additional * price
    fee = gross * config.fee_rate
    total = gross + fee
    if total > state.cash:
        affordable = state.cash / (price * (Decimal("1") + config.fee_rate))
        gross = affordable * price
        fee = gross * config.fee_rate
        additional = affordable
        total = gross + fee

    return BacktestState(cash=state.cash - total, quantity=state.quantity + additional)
