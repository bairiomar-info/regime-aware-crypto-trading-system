from datetime import datetime, timedelta, timezone
from decimal import Decimal

from trading_system.backtest.engine import BacktestConfig, MarketBar
from trading_system.backtest.oos_runner import run_oos_backtests
from trading_system.backtest.walk_forward import WalkForwardWindow
from trading_system.strategies.models import SignalDirection, StrategySignal


def test_long_signal_executes_on_next_bar_open() -> None:
    start = datetime(2026, 9, 16, tzinfo=timezone.utc)
    bars = tuple(
        MarketBar(
            timestamp=start + timedelta(hours=i),
            open=Decimal(str(value[0])),
            close=Decimal(str(value[1])),
        )
        for i, value in enumerate(((100, 100), (110, 115), (120, 120)))
    )
    window = WalkForwardWindow(train=(bars[0],), test=bars[1:])

    def signal_factory(decision_bar, history):
        return StrategySignal(
            decision_time=decision_bar.timestamp,
            direction=SignalDirection.LONG,
            target_weight=Decimal("1"),
        )

    result = run_oos_backtests(
        (window,),
        signal_factory,
        BacktestConfig(initial_cash=Decimal("1000"), fee_rate=Decimal("0"), slippage_rate=Decimal("0")),
    )[0]

    # The signal is decided on the first OOS bar and executes on the second OOS bar's open (120).
    # With the test strategy remaining LONG, the final marked equity is 1000 * 120 / 120 = 1000.
    assert result.final_equity == Decimal("1000")
    assert result.final_equity.is_finite()
