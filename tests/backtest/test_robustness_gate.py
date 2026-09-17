from decimal import Decimal

from trading_system.backtest.robustness import SensitivityResult
from trading_system.backtest.robustness_gate import RobustnessGateConfig, evaluate_robustness_gate
from trading_system.backtest.robustness_matrix import RobustnessCaseResult, RobustnessMatrix
from trading_system.backtest.robustness_report import RobustnessSummary


def matrix(results: tuple[SensitivityResult, ...]) -> RobustnessMatrix:
    cases = tuple(
        RobustnessCaseResult(result.name, "params", "cost", result) for result in results
    )
    return RobustnessMatrix(cases, RobustnessSummary(
        case_count=len(results),
        min_return=min(item.total_return for item in results),
        max_drawdown=max(item.max_drawdown for item in results),
        median_return=sorted(item.total_return for item in results)[len(results) // 2],
        positive_return_fraction=Decimal(sum(item.total_return > 0 for item in results)) / Decimal(len(results)),
    ))


def test_gate_passes_when_explicit_thresholds_are_met() -> None:
    result = evaluate_robustness_gate(
        matrix((
            SensitivityResult("a", Decimal("0.10"), Decimal("0.10")),
            SensitivityResult("b", Decimal("0.02"), Decimal("0.20")),
        )),
        RobustnessGateConfig(min_positive_case_fraction=Decimal("0.50"), max_worst_drawdown=Decimal("0.20")),
    )
    assert result.passed is True
    assert result.failures == ()


def test_gate_reports_each_failed_threshold() -> None:
    result = evaluate_robustness_gate(
        matrix((SensitivityResult("a", Decimal("-0.10"), Decimal("0.40")),)),
    )
    assert result.passed is False
    assert "positive_case_fraction_below_threshold" in result.failures
    assert "worst_drawdown_above_threshold" in result.failures
