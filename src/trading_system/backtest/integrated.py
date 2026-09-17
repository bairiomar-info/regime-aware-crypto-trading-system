"""End-to-end causal single-asset strategy backtest orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_system.compliance.classification import AssetCompliance
from trading_system.execution.gate import PreTradeConfig, validate_pre_trade
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import AssetBalance, PortfolioState
from trading_system.strategies.interface import ResearchStrategy, evaluate_strategy
from trading_system.strategies.models import SignalDirection, StrategyContext, StrategySignal

from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .results import BacktestResult, EquityPoint


@dataclass(frozen=True)
class IntegratedBacktestInput:
    bars: tuple[MarketBar, ...]
    contexts: tuple[StrategyContext, ...]
    asset_compliance: AssetCompliance | None = None


def _portfolio_state(state: BacktestState, symbol: str) -> PortfolioState:
    balances = () if state.quantity == 0 else (AssetBalance(symbol, state.quantity),)
    return PortfolioState(state.cash, balances)


def _pre_trade_order(state: BacktestState, signal: StrategySignal, execution_bar: MarketBar, config: BacktestConfig) -> tuple[OrderIntent | None, Decimal]:
    buy_price = execution_bar.open * (Decimal("1") + config.slippage_rate)
    sell_price = execution_bar.open * (Decimal("1") - config.slippage_rate)
    equity = state.cash + state.quantity * sell_price
    target_quantity = equity * signal.target_weight / buy_price
    delta = target_quantity - state.quantity
    if delta > 0:
        return OrderIntent(signal.symbol, OrderSide.BUY, delta * buy_price, "strategy_target_increase"), buy_price
    if delta < 0:
        sold = min(-delta, state.quantity)
        return OrderIntent(signal.symbol, OrderSide.SELL, sold * sell_price, "strategy_target_decrease"), sell_price
    return None, buy_price


def _execute_integrated_signal(
    state: BacktestState,
    signal: StrategySignal,
    execution_bar: MarketBar,
    config: BacktestConfig,
    pre_trade_config: PreTradeConfig,
    asset_compliance: AssetCompliance | None,
) -> BacktestState:
    if signal.direction is SignalDirection.NO_TRADE:
        return state
    if signal.direction is not SignalDirection.LONG:
        raise ValueError("only LONG and NO_TRADE are supported")
    if asset_compliance is None:
        raise ValueError("asset_compliance is required for executable LONG signals")
    order, price = _pre_trade_order(state, signal, execution_bar, config)
    if order is not None:
        validate_pre_trade(
            _portfolio_state(state, signal.symbol),
            order,
            price,
            pre_trade_config,
            prices={signal.symbol: price},
            asset_compliance=asset_compliance,
        )
    return execute_signal(state, signal, execution_bar, config)


def run_strategy_backtest(
    strategy: ResearchStrategy,
    data: IntegratedBacktestInput,
    config: BacktestConfig,
    *,
    pre_trade_config: PreTradeConfig = PreTradeConfig(),
) -> BacktestResult:
    """Evaluate point-in-time contexts and execute signals on the next bar.

    Signals are queued at their decision timestamp and applied at the next
    bar's open before that bar is marked to market. Thus the equity curve never
    contains information from a future execution while still reflecting fills
    at their actual execution timestamp.
    """
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
    pending: StrategySignal | None = None

    for index, bar in enumerate(data.bars):
        if pending is not None:
            state = _execute_integrated_signal(
                state, pending, bar, config, pre_trade_config, data.asset_compliance
            )

        curve.append(EquityPoint(bar.timestamp, state.cash + state.quantity * bar.close))

        signal = by_time.get(bar.timestamp)
        if signal is not None:
            if index + 1 >= len(data.bars):
                if signal.direction is SignalDirection.LONG:
                    raise ValueError("final-bar LONG signal has no executable next bar")
                pending = None
            else:
                pending = signal
        else:
            pending = None

    peak = curve[0].equity
    max_dd = Decimal("0")
    for point in curve:
        peak = max(peak, point.equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - point.equity) / peak)
    final = curve[-1].equity
    return BacktestResult(config.initial_cash, state.cash, state.quantity, final, final / config.initial_cash - Decimal("1"), max_dd, tuple(curve))
