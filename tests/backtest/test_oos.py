from datetime import datetime, timedelta, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.oos import run_oos_windows
from trading_system.backtest.walk_forward import WalkForwardWindow
from trading_system.strategies.models import SignalDirection, StrategySignal


def test_oos_runner_executes_test_windows_only() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = tuple(MarketBar(start + timedelta(days=i), Decimal("100"), Decimal(str(100 + i * 10))) for i in range(6))
    windows = (WalkForwardWindow(train=bars[:2], test=bars[2:]),)

    def signals(bar: MarketBar, history: tuple[MarketBar, ...]) -> StrategySignal:
        long = len(history) == 1
        return StrategySignal(
            bar.timestamp,
            "BTCUSDT",
            SignalDirection.LONG if long else SignalDirection.NO_TRADE,
            "test",
            target_weight=Decimal("1") if long else None,
        )

    aggregate = run_oos_windows(windows, bars, signals, BacktestConfig(initial_cash=Decimal("100")))
    assert len(aggregate.windows) == 1
    assert aggregate.windows[0].result.initial_cash == Decimal("100")
    assert aggregate.total_return == Decimal("0.5")
