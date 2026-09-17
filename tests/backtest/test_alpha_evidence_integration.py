from decimal import Decimal

import pytest

from trading_system.backtest.alpha_evidence import evaluate_alpha_evidence
from trading_system.backtest.alpha_gate import AlphaGateConfig
from trading_system.backtest.regime_stability import RegimeOOSResult
from trading_system.backtest.robustness_report import RobustnessSummary


def _summary(cases: int = 5, positive: str = "0.80", drawdown: str = "0.20") -> RobustnessSummary:
    return RobustnessSummary(
        case_count=cases,
        min_return=Decimal("0.01"),
        max_drawdown=Decimal(drawdown),
        median_return=Decimal("0.02"),
        positive_return_fraction=Decimal(positive),
    )


def _regime(name: str, worst: str) -> RegimeOOSResult:
    return RegimeOOSResult(name, 2, Decimal("1"), Decimal(worst), Decimal(worst), Decimal("0.10"))


def test_alpha_evidence_integrates_gate_and_regime_evidence() -> None:
    evidence = evaluate_alpha_evidence(_summary(), (_regime("bear", "0.01"), _regime("bull", "0.03")), oos_window_count=4, worst_oos_return=Decimal("0.005"))
    assert evidence.gate.passed
    assert evidence.worst_regime_return == Decimal("0.01")
    assert evidence.all_oos_windows_positive
    assert evidence.all_regimes_positive


def test_negative_oos_return_is_preserved_as_failure_evidence() -> None:
    evidence = evaluate_alpha_evidence(_summary(), (_regime("bull", "0.02"),), oos_window_count=3, worst_oos_return=Decimal("-0.01"))
    assert evidence.gate.passed
    assert not evidence.all_oos_windows_positive


def test_negative_regime_return_is_preserved_as_failure_evidence() -> None:
    evidence = evaluate_alpha_evidence(_summary(), (_regime("bull", "0.01"), _regime("bear", "-0.02")), oos_window_count=3, worst_oos_return=Decimal("0.01"))
    assert not evidence.all_regimes_positive
    assert evidence.worst_regime_return == Decimal("-0.02")


def test_invalid_oos_window_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="oos_window_count"):
        evaluate_alpha_evidence(_summary(), (_regime("bull", "0.01"),), 0, Decimal("0.01"))


def test_missing_regimes_are_rejected() -> None:
    with pytest.raises(ValueError, match="regimes"):
        evaluate_alpha_evidence(_summary(), (), 2, Decimal("0.01"))


def test_gate_rejection_remains_distinct_from_positive_oos_evidence() -> None:
    evidence = evaluate_alpha_evidence(_summary(cases=5), (_regime("bull", "0.01"),), oos_window_count=2, worst_oos_return=Decimal("0.01"), config=AlphaGateConfig(min_cases=10))
    assert not evidence.gate.passed
    assert evidence.all_oos_windows_positive
