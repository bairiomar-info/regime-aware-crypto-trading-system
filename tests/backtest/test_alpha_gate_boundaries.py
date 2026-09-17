from decimal import Decimal

from trading_system.backtest.alpha_gate import AlphaGateConfig, evaluate_alpha_gate
from trading_system.backtest.robustness_report import RobustnessSummary


def _summary(cases: int, positive: str, drawdown: str) -> RobustnessSummary:
    return RobustnessSummary(
        case_count=cases,
        min_return=Decimal("0.01"),
        max_drawdown=Decimal(drawdown),
        median_return=Decimal("0.02"),
        positive_return_fraction=Decimal(positive),
    )


def test_gate_passes_exactly_at_all_default_thresholds() -> None:
    result = evaluate_alpha_gate(_summary(5, "0.60", "0.30"))
    assert result.passed
    assert result.sufficient_cases
    assert result.sufficient_positive_fraction
    assert result.acceptable_drawdown


def test_gate_fails_when_case_count_is_one_below_threshold() -> None:
    result = evaluate_alpha_gate(_summary(4, "0.60", "0.30"))
    assert not result.passed
    assert not result.sufficient_cases


def test_gate_fails_when_positive_fraction_is_one_tick_below_threshold() -> None:
    result = evaluate_alpha_gate(_summary(5, "0.5999", "0.30"))
    assert not result.passed
    assert not result.sufficient_positive_fraction


def test_gate_fails_when_drawdown_exceeds_threshold() -> None:
    result = evaluate_alpha_gate(_summary(5, "0.60", "0.3001"))
    assert not result.passed
    assert not result.acceptable_drawdown


def test_custom_thresholds_are_applied_independently() -> None:
    config = AlphaGateConfig(
        min_cases=10,
        min_positive_fraction=Decimal("0.80"),
        max_drawdown=Decimal("0.20"),
    )
    result = evaluate_alpha_gate(_summary(10, "0.80", "0.20"), config)
    assert result.passed
