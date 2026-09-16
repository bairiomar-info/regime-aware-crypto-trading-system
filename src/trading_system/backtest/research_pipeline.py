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
from .robustness_report import RobustnessSummary
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
    results = run_oos_backtests(windows, signal_factory, config.backtest)
    if not results:
        raise ValueError("research run produced no OOS windows")

    window_results = tuple(
        OOSWindowResult(index, result.total_return, result.max_drawdown)
        for index, result in enumerate(results)
    )
    regime_inputs = tuple(
        (regime_labels[bars.index(window.test[0])], window_results[index])
        for index, window in enumerate(windows)
    )
    regimes: tuple[RegimeOOSResult, ...] = analyze_by_regime(regime_inputs)

    returns = tuple(item.total_return for item in window_results)
    ordered = tuple(sorted(returns))
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / Decimal("2")
    positive = sum(value > 0 for value in returns)
    robustness = RobustnessSummary(
        case_count=len(window_results),
        min_return=min(returns),
        max_drawdown=max(item.max_drawdown for item in window_results),
        median_return=median,
        positive_return_fraction=Decimal(positive) / Decimal(len(returns)),
    )

    return evaluate_alpha_evidence(
        summary=robustness,
        regimes=regimes,
        oos_window_count=len(window_results),
        worst_oos_return=min(returns),
        config=config.alpha_gate,
    )
