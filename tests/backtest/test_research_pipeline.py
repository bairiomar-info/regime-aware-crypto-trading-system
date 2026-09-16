from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.research_pipeline import ResearchRunConfig, run_research_pipeline
from trading_system.strategies.models import SignalDirection, StrategySignal


def _bars(count: int = 6) -> tuple[MarketBar, ...]:
    start = datetime(2026, 9, 16, tzinfo=timezone.utc)
    return tuple(
        MarketBar(
            timestamp=start + timedelta(hours=i),
            open=Decimal(100 + i),
            close=Decimal(100 + i),
        )
        for i in range(count)
    )


def _config() -> ResearchRunConfig:
    return ResearchRunConfig(
        train_size=2,
        test_size=2,
        step=2,
        backtest=BacktestConfig(
            initial_cash=Decimal("1000"), fee_rate=Decimal("0"), slippage_rate=Decimal("0")
        ),
    )


def test_full_research_pipeline_produces_alpha_evidence() -> None:
    bars = _bars()
    labels = ("bull", "bull", "bear", "bear", "bull", "bull")

    def signal_factory(decision_bar, history):
        return StrategySignal(
            decision_time=decision_bar.timestamp,
            direction=SignalDirection.NO_TRADE,
            target_weight=None,
        )

    evidence = run_research_pipeline(bars, signal_factory, _config(), labels)

    assert evidence.gate.passed is False
    assert evidence.oos_window_count == 2
    assert evidence.worst_oos_return == Decimal("0")
    assert evidence.all_oos_windows_positive is False
    assert evidence.all_regimes_positive is False


def test_pipeline_rejects_mismatched_regime_labels() -> None:
    with pytest.raises(ValueError, match="equal length"):
        run_research_pipeline(_bars(), lambda *_: None, _config(), ("bull",))


def test_pipeline_rejects_configuration_that_produces_no_oos_windows() -> None:
    with pytest.raises(ValueError):
        run_research_pipeline(_bars(3), lambda *_: None, ResearchRunConfig(
            train_size=3,
            test_size=3,
            step=1,
            backtest=_config().backtest,
        ), ("bull", "bull", "bull"))
