from datetime import datetime, timedelta, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.oos_runner import run_oos_backtests
from trading_system.backtest.walk_forward import WalkForwardWindow
from trading_system.strategies.models import SignalDirection, StrategySignal


def _bars() -> tuple[MarketBar, ...]:
    start = datetime(2026, 9, 16, tzinfo=timezone.utc)
    return tuple(
        MarketBar(
            timestamp=start + timedelta(hours=index),
            open=Decimal(str(100 + index)),
            close=Decimal(str(100 + index)),
        )
        for index in range(3)
    )


def test_oos_runner_executes_real_test_segment_causally() -> None:
    bars = _bars()
    window = WalkForwardWindow(
        train=(bars[0],),
        test=bars[1:],
    )

    def signal_factory(decision_bar, history):
        return StrategySignal(
            decision_time=decision_bar.timestamp,
            direction=SignalDirection.NO_TRADE,
            target_weight=None,
        )

    results = run_oos_backtests(
        (window,),
        signal_factory,
        BacktestConfig(initial_cash=Decimal("1000")),
    )

    assert len(results) == 1
    assert results[0].initial_cash == Decimal("1000")
    assert results[0].final_equity == Decimal("1000")
