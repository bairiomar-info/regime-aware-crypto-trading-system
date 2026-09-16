"""Explicit orchestration boundary for a deterministic OOS research run."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Sequence

from .alpha_evidence import AlphaEvidence, evaluate_alpha_evidence
from .alpha_gate import AlphaGateConfig
from .backtest.engine import BacktestConfig, MarketBar
from .backtest.oos_runner import run_oos_backtests
from .backtest.regime_stability import RegimeOOSResult, analyze_by_regime
from .backtest.walk_forward import WalkForwardWindow, make_walk_forward_windows
from .data.models import Instrument, Timeframe


@dataclass(frozen=True)
class ResearchRunConfig:
    train_size: int
    test_size: int
    step: int
    backtest: BacktestConfig
    alpha_gate: AlphaGateConfig = AlphaGateConfig()


def run_research_pipeline(
    bars: Sequence[MarketBar],
    signal_factory: Callable,
    config: ResearchRunConfig,
    regime_labels: Sequence[str],
) -> AlphaEvidence:
    """Run the complete deterministic OOS evidence path from bars to gate."""
    if len(bars) != len(regime_labels):
        raise ValueError("bars and regime_labels must have equal length")
    windows = make_walk_forward_windows(
        bars,
        train_size=config.train_size,
        test_size=config.test_size,
        step=config.step,
    )
    results = run_oos_backtests(windows, signal_factory, config.backtest)
    window_results = tuple(result for experiment in results for result in experiment.windows)
    regime_inputs = tuple(
        (regime_labels[bar_index], window_result)
        for bar_index, window_result in enumerate(window_results)
    )
    regimes: tuple[RegimeOOSResult, ...] = analyze_by_regime(regime_inputs)
    return evaluate_alpha_evidence(
        robustness=__import__("trading_system.backtest.robustness_report", fromlist=["summarize_robustness"]).summarize_robustness(
            tuple(window_results)
        ),
        regimes=regimes,
        oos_window_count=len(window_results),
        worst_oos_return=min((item.total_return for item in window_results), default=Decimal("0")),
        config=config.alpha_gate,
    )
