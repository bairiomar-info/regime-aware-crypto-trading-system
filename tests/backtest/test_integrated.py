from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.integrated import IntegratedBacktestInput, run_strategy_backtest
from trading_system.compliance.classification import AssetCompliance
from trading_system.features.models import FeatureSnapshot
from trading_system.strategies.momentum import TimeSeriesMomentum, TimeSeriesMomentumConfig
from trading_system.strategies.models import StrategyContext


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


def _compliance() -> AssetCompliance:
    return AssetCompliance("BTCUSDT", Decimal("0"))


def test_integrated_strategy_backtest_respects_next_bar_execution() -> None:
    bars = (
        MarketBar(datetime(2026, 1, 1, 0, tzinfo=timezone.utc), Decimal("100"), Decimal("100")),
        MarketBar(datetime(2026, 1, 1, 1, tzinfo=timezone.utc), Decimal("110"), Decimal("110")),
        MarketBar(datetime(2026, 1, 1, 2, tzinfo=timezone.utc), Decimal("110"), Decimal("120")),
    )
    contexts = (
        StrategyContext(
            decision_time=bars[1].timestamp,
            symbol="BTCUSDT",
            features=_features(bars[1].timestamp),
            price_history=((bars[0].timestamp, Decimal("100")), (bars[1].timestamp, Decimal("110"))),
        ),
    )
    strategy = TimeSeriesMomentum(TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1")))
    result = run_strategy_backtest(
        strategy,
        IntegratedBacktestInput(bars, contexts, asset_compliance=_compliance()),
        BacktestConfig(Decimal("1000")),
    )
    # Signal is evaluated at t=1 and therefore can only execute at t=2 open.
    assert result.equity_curve[1].equity == Decimal("1000")
    assert result.final_equity == Decimal("1090.909090909090909090909091")


def test_terminal_no_trade_signal_does_not_require_next_bar() -> None:
    bars = tuple(
        MarketBar(datetime(2026, 1, 1, h, tzinfo=timezone.utc), Decimal("100"), Decimal("100"))
        for h in (0, 1)
    )
    contexts = (
        StrategyContext(
            decision_time=bars[-1].timestamp,
            symbol="BTCUSDT",
            features=_features(bars[-1].timestamp),
            price_history=((bars[0].timestamp, Decimal("100")), (bars[-1].timestamp, Decimal("100"))),
        ),
    )
    strategy = TimeSeriesMomentum(
        TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1"), min_return=Decimal("0"))
    )

    result = run_strategy_backtest(strategy, IntegratedBacktestInput(bars, contexts), BacktestConfig(Decimal("1000")))

    assert result.final_equity == Decimal("1000")


def test_terminal_long_signal_requires_next_bar() -> None:
    bars = tuple(
        MarketBar(datetime(2026, 1, 1, h, tzinfo=timezone.utc), Decimal(str(price)), Decimal(str(price)))
        for h, price in ((0, 100), (1, 110))
    )
    contexts = (
        StrategyContext(
            decision_time=bars[-1].timestamp,
            symbol="BTCUSDT",
            features=_features(bars[-1].timestamp),
            price_history=((bars[0].timestamp, Decimal("100")), (bars[-1].timestamp, Decimal("110"))),
        ),
    )
    strategy = TimeSeriesMomentum(TimeSeriesMomentumConfig(lookback=1, target_weight=Decimal("1")))

    with pytest.raises(ValueError, match="final-bar LONG signal has no executable next bar"):
        run_strategy_backtest(
            strategy,
            IntegratedBacktestInput(bars, contexts, asset_compliance=_compliance()),
            BacktestConfig(Decimal("1000")),
        )
