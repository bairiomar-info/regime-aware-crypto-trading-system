"""Backtesting public API."""

from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .evaluation import OOSSummary, OOSWindowResult, summarize_oos
from .results import BacktestResult, EquityPoint, calculate_max_drawdown, calculate_total_return
from .walk_forward import WalkForwardWindow, make_walk_forward_windows

__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "BacktestState",
    "EquityPoint",
    "MarketBar",
    "OOSSummary",
    "OOSWindowResult",
    "WalkForwardWindow",
    "calculate_max_drawdown",
    "calculate_total_return",
    "execute_signal",
    "make_walk_forward_windows",
    "summarize_oos",
]
