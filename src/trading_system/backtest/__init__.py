"""Backtesting public API."""

from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .evaluation import OOSSummary, OOSWindowResult, summarize_oos
from .metrics import max_drawdown, mean_return, sharpe_ratio, simple_returns, volatility
from .parameter_sensitivity import MomentumParameterCase, make_momentum_parameter_cases, summarize_parameter_sensitivity
from .results import BacktestResult, EquityPoint, calculate_max_drawdown, calculate_total_return
from .robustness import SensitivityCase, SensitivityResult, make_cost_sensitivity_cases, summarize_sensitivity
from .robustness_report import RobustnessSummary, summarize_results
from .runner import SignalFactory, run_backtest
from .walk_forward import WalkForwardWindow, make_walk_forward_windows

__all__ = [
    "BacktestConfig", "BacktestResult", "BacktestState", "EquityPoint", "MarketBar",
    "MomentumParameterCase", "OOSSummary", "OOSWindowResult", "RobustnessSummary",
    "SensitivityCase", "SensitivityResult", "SignalFactory", "WalkForwardWindow",
    "calculate_max_drawdown", "calculate_total_return", "execute_signal",
    "make_cost_sensitivity_cases", "make_momentum_parameter_cases", "make_walk_forward_windows",
    "max_drawdown", "mean_return", "run_backtest", "sharpe_ratio", "simple_returns",
    "summarize_oos", "summarize_parameter_sensitivity", "summarize_results", "summarize_sensitivity", "volatility",
]
