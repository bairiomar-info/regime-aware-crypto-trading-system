"""Backtesting public API."""

from .alpha_evidence import AlphaEvidence, evaluate_alpha_evidence
from .alpha_gate import AlphaGateConfig, AlphaGateResult, evaluate_alpha_gate
from .engine import BacktestConfig, BacktestState, MarketBar, execute_signal
from .evaluation import OOSSummary, OOSWindowResult, summarize_oos
from .experiment_manifest import ExperimentManifest
from .experiment_result import ExperimentResult, bind_result_to_manifest, fingerprint_experiment_result, serialize_experiment_result
from .metrics import max_drawdown, mean_return, sharpe_ratio, simple_returns, volatility
from .oos_experiments import OOSExperimentResult, run_oos_experiments
from .parameter_sensitivity import MomentumParameterCase, make_momentum_parameter_cases, summarize_parameter_sensitivity
from .regime_stability import RegimeOOSResult, analyze_by_regime
from .results import BacktestResult, EquityPoint, calculate_max_drawdown, calculate_total_return
from .robustness import SensitivityCase, SensitivityResult, make_cost_sensitivity_cases, summarize_sensitivity
from .robustness_matrix import RobustnessCaseResult, RobustnessMatrix, run_momentum_cost_matrix
from .robustness_report import RobustnessSummary, summarize_results
from .runner import SignalFactory, run_backtest
from .stability import OOSStability, analyze_oos_stability
from .walk_forward import WalkForwardWindow, make_walk_forward_windows

__all__ = [
    "AlphaEvidence", "AlphaGateConfig", "AlphaGateResult", "BacktestConfig", "BacktestResult", "BacktestState",
    "EquityPoint", "ExperimentManifest", "ExperimentResult", "MarketBar", "MomentumParameterCase", "OOSExperimentResult",
    "OOSStability", "OOSSummary", "OOSWindowResult", "RegimeOOSResult", "RobustnessCaseResult", "RobustnessMatrix",
    "RobustnessSummary", "SensitivityCase", "SensitivityResult", "SignalFactory", "WalkForwardWindow",
    "analyze_by_regime", "analyze_oos_stability", "bind_result_to_manifest", "calculate_max_drawdown", "calculate_total_return",
    "evaluate_alpha_evidence", "evaluate_alpha_gate", "execute_signal", "fingerprint_experiment_result", "make_cost_sensitivity_cases",
    "make_momentum_parameter_cases", "make_walk_forward_windows", "max_drawdown", "mean_return", "run_backtest", "run_momentum_cost_matrix",
    "run_oos_experiments", "serialize_experiment_result", "sharpe_ratio", "simple_returns", "summarize_oos", "summarize_parameter_sensitivity",
    "summarize_results", "summarize_sensitivity", "volatility",
]
