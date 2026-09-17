from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.integrated import IntegratedBacktestInput, run_strategy_backtest
from trading_system.compliance.classification import AssetCompliance
from trading_system.execution.gate import PreTradeConfig
from trading_system.features.models import FeatureSnapshot
from trading_system.portfolio.orders import OrderIntent, OrderSide
from trading_system.portfolio.state import PortfolioState
from trading_system.risk.limits import RiskLimits, validate_order_risk
from trading_system.strategies.momentum import TimeSeriesMomentum, TimeSeriesMomentumConfig
from trading_system.strategies.models import SignalDirection, StrategyContext, StrategySignal


def _features(at: datetime) -> FeatureSnapshot:
    return FeatureSnapshot(
        decision_time=at,
        trend_score=None,
        realized_volatility=None,
        breadth=None,
        cross_sectional_dispersion=None,
        average_pairwise_correlation=None,
        asset_count=1,
    )


def _context(at: datetime, prices: tuple[tuple[datetime, str], ...]) -> StrategyContext:
    return StrategyContext(
        decision_time=at,
        symbol="BTCUSDT",
        features=_features(at),
        price_history=tuple((timestamp, Decimal(price)) for timestamp, price in prices),
    )


def _bars(*prices: tuple[int, str]) -> tuple[MarketBar, ...]:
    return tuple(
        MarketBar(datetime(2026, 1, 1, hour, tzinfo=timezone.utc), Decimal(price), Decimal(price))
        for hour, price in prices
    )


def test_integrated_backtest_rejects_out_of_order_contexts() -> None:
    bars = _bars((0, "100"), (1, "101"), (2, "102"))
    contexts = (
        _context(bars[1].timestamp, ((bars[0].timestamp, "100"), (bars[1].timestamp, "101"))),
        _context(bars[0].timestamp, ((bars[0].timestamp, "100"),)),
    )
    strategy = TimeSeriesMomentum(TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1")))
    with pytest.raises(ValueError, match="contexts must be strictly chronological"):
        run_strategy_backtest(strategy, IntegratedBacktestInput(bars, contexts), BacktestConfig(Decimal("1000")))


def test_integrated_backtest_requires_explicit_compliance_for_long() -> None:
    bars = _bars((0, "100"), (1, "101"), (2, "102"))
    context = _context(
        bars[1].timestamp,
        ((bars[0].timestamp, "100"), (bars[1].timestamp, "101")),
    )
    strategy = TimeSeriesMomentum(TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1")))
    with pytest.raises(ValueError, match="asset_compliance is required"):
        run_strategy_backtest(strategy, IntegratedBacktestInput(bars, (context,)), BacktestConfig(Decimal("1000")))


def test_integrated_backtest_blocks_noncompliant_asset_before_execution() -> None:
    bars = _bars((0, "100"), (1, "101"), (2, "102"))
    context = _context(
        bars[1].timestamp,
        ((bars[0].timestamp, "100"), (bars[1].timestamp, "101")),
    )
    strategy = TimeSeriesMomentum(TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1")))
    with pytest.raises(ValueError, match="interest-income threshold"):
        run_strategy_backtest(
            strategy,
            IntegratedBacktestInput(
                bars,
                (context,),
                asset_compliance=AssetCompliance("BTCUSDT", Decimal("0.051")),
            ),
            BacktestConfig(Decimal("1000")),
        )


def test_risk_gate_rejects_order_above_position_limit() -> None:
    state = PortfolioState(Decimal("1000"), ())
    order = OrderIntent("BTCUSDT", OrderSide.BUY, Decimal("900"), "test")
    with pytest.raises(ValueError, match="max_position_weight"):
        validate_order_risk(
            state,
            order,
            Decimal("100"),
            RiskLimits(max_position_weight=Decimal("0.50"), max_order_notional=Decimal("1"), max_gross_exposure=Decimal("1")),
            prices={"BTCUSDT": Decimal("100")},
        )


def test_momentum_warmup_is_explicit_and_deterministic() -> None:
    bars = _bars((0, "100"), (1, "110"), (2, "120"))
    strategy = TimeSeriesMomentum(TimeSeriesMomentumConfig(lookback=2, target_weight=Decimal("1")))
    signal = strategy.generate_signal(_context(bars[1].timestamp, ((bars[0].timestamp, "100"), (bars[1].timestamp, "110"))))
    assert signal.direction is SignalDirection.NO_TRADE
    assert signal.reason == "insufficient_price_history"
    signal = strategy.generate_signal(
        _context(
            bars[2].timestamp,
            ((bars[0].timestamp, "100"), (bars[1].timestamp, "110"), (bars[2].timestamp, "120")),
        )
    )
    assert signal.direction is SignalDirection.LONG
    assert signal.score == Decimal("0.2")


def test_pre_trade_config_remains_explicit_at_integration_boundary() -> None:
    assert isinstance(PreTradeConfig(), PreTradeConfig)
    signal = StrategySignal(
        datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        "BTCUSDT",
        SignalDirection.NO_TRADE,
        "test",
    )
    assert signal.target_weight is None
