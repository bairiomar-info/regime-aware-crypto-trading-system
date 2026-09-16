"""Explicit orchestration boundary for a deterministic OOS research run."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Sequence

from .alpha_evidence import AlphaEvidence, evaluate_alpha_evidence
from .alpha_gate import AlphaGateConfig
from .engine import BacktestConfig, MarketBar
from .evaluation import OOSWindowResult
from .oos_runner import run_oos_backtests
from .regime_stability import RegimeOOSResult, analyze_by_regime
from .robustness_report import summarize_robustness
from .walk_forward import make_walk_forward_windows


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
    experiments = run_oos_backtests(windows, signal_factory, config.backtest)
    window_results: tuple[OOSWindowResult, ...] = tuple(
        window for experiment in experiments for window in experiment.windows
    )
    if not window_results:
        raise ValueError("research run produced no OOS windows")

    # Each OOS result corresponds to one walk-forward test segment. Use the
    # first bar of that segment to assign its point-in-time regime label.
    regime_inputs: list[tuple[str, OOSWindowResult]] = []
    for index, window in enumerate(windows):
        if index >= len(window_results):
            break
        regime_inputs.append((regime_labels[bars.index(window.test[0])], window_results[index]))

    regimes: tuple[RegimeOOSResult, ...] = analyze_by_regime(tuple(regime_inputs))
    robustness = summarize_robustness(window_results)
    return evaluate_alpha_evidence(
        robustness=robustness,
        regimes=regimes,
        oos_window_count=len(window_results),
        worst_oos_return=min(item.total_return for item in window_results),
        config=config.alpha_gate,
    )
