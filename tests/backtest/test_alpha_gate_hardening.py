from decimal import Decimal

import pytest

from trading_system.backtest.alpha_gate import AlphaGateConfig, evaluate_alpha_gate
from trading_system.backtest.robustness_report import RobustnessSummary


def summary(**overrides: object) -> RobustnessSummary:
    values: dict[str, object] = {
        "case_count": 5,
        "min_return": Decimal("-0.05"),
        "max_drawdown": Decimal("0.20"),
        "median_return": Decimal("0.03"),
        "positive_return_fraction": Decimal("0.80"),
    }
    values.update(overrides)
    return RobustnessSummary(**values)  # type: ignore[arg-type]


def test_alpha_gate_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="min_cases"):
        AlphaGateConfig(min_cases=0)
    with pytest.raises(ValueError, match="positive_fraction"):
        AlphaGateConfig(min_positive_fraction=Decimal("1.1"))
    with pytest.raises(ValueError, match="max_drawdown"):
        AlphaGateConfig(max_drawdown=Decimal("NaN"))


def test_alpha_gate_rejects_non_finite_evidence() -> None:
    with pytest.raises(ValueError, match="summary.min_return"):
        evaluate_alpha_gate(summary(min_return=Decimal("NaN")))
    with pytest.raises(ValueError, match="positive_return_fraction"):
        evaluate_alpha_gate(summary(positive_return_fraction=Decimal("1.1")))


def test_alpha_gate_rejects_negative_drawdown() -> None:
    with pytest.raises(ValueError, match="max_drawdown"):
        evaluate_alpha_gate(summary(max_drawdown=Decimal("-0.01")))


def test_alpha_gate_passes_valid_evidence() -> None:
    result = evaluate_alpha_gate(summary())
    assert result.passed is True
    assert result.sufficient_cases is True
    assert result.sufficient_positive_fraction is True
    assert result.acceptable_drawdown is True
