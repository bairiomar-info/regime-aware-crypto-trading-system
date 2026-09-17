from decimal import Decimal

import pytest

from trading_system.backtest.oos_evidence import (
    evaluate_completed_oos_alpha_evidence,
    evaluate_oos_alpha_evidence,
    summarize_oos_experiments,
)
from trading_system.backtest.oos_experiments import OOSExperimentResult
from trading_system.backtest.evaluation import OOSWindowResult
from trading_system.backtest.regime_stability import RegimeOOSResult


def _experiment(name: str, returns: tuple[str, ...], compounded: str = "0.10", drawdown: str = "0.05") -> OOSExperimentResult:
    windows = tuple(
        OOSWindowResult(
            window_index=index,
            total_return=Decimal(value),
            max_drawdown=Decimal(drawdown),
        )
        for index, value in enumerate(returns)
    )
    return OOSExperimentResult(
        case_name=name,
        windows=windows,
        compounded_return=Decimal(compounded),
        worst_drawdown=Decimal(drawdown),
    )


def _regime(name: str, worst: str) -> RegimeOOSResult:
    return RegimeOOSResult(
        regime=name,
        window_count=2,
        positive_window_fraction=Decimal("1"),
        mean_return=Decimal("0.05"),
        worst_return=Decimal(worst),
        worst_drawdown=Decimal("0.05"),
    )


def test_oos_evidence_requires_consistent_window_counts() -> None:
    experiments = (_experiment("a", ("0.01",)), _experiment("b", ("0.01", "0.02")))
    with pytest.raises(ValueError, match="same OOS window count"):
        summarize_oos_experiments(experiments)


def test_completed_oos_evidence_derives_gate_inputs_from_experiments() -> None:
    experiments = tuple(
        _experiment(f"case-{index}", ("0.01", "0.02"), compounded="0.03", drawdown="0.05")
        for index in range(5)
    )
    evidence = evaluate_completed_oos_alpha_evidence(
        experiments,
        (_regime("bull", "0.01"), _regime("bear", "0.02")),
    )
    assert evidence.gate.passed
    assert evidence.gate.sufficient_cases
    assert evidence.gate.sufficient_positive_fraction
    assert evidence.gate.acceptable_drawdown
    assert evidence.oos_window_count == 10
    assert evidence.worst_oos_return == Decimal("0.01")
    assert evidence.all_oos_windows_positive
    assert evidence.all_regimes_positive


def test_one_negative_oos_window_is_preserved_in_completed_evidence() -> None:
    experiments = tuple(
        _experiment(f"case-{index}", ("0.01", "-0.01"), compounded="0", drawdown="0.10")
        for index in range(5)
    )
    evidence = evaluate_completed_oos_alpha_evidence(experiments, (_regime("bull", "0.01"),))
    assert evidence.gate.passed is False
    assert evidence.worst_oos_return == Decimal("-0.01")
    assert not evidence.all_oos_windows_positive


def test_duplicate_experiment_names_are_rejected() -> None:
    experiments = (_experiment("case", ("0.01",)), _experiment("case", ("0.02",)))
    with pytest.raises(ValueError, match="case_name values must be unique"):
        summarize_oos_experiments(experiments)


def test_supplied_summary_path_still_enforces_window_consistency() -> None:
    experiments = (_experiment("a", ("0.01",)), _experiment("b", ("0.02",)))
    evidence = evaluate_oos_alpha_evidence(
        summary=summarize_oos_experiments(experiments),
        experiments=experiments,
        regimes=(_regime("bull", "0.01"),),
    )
    assert evidence.oos_window_count == 2
