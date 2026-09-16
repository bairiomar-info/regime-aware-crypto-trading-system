from decimal import Decimal

from trading_system.backtest.robustness import SensitivityResult
from trading_system.backtest.robustness_report import summarize_results


def test_summarize_results_is_deterministic() -> None:
    results = (
        SensitivityResult("a", Decimal("0.10"), Decimal("0.05")),
        SensitivityResult("b", Decimal("-0.02"), Decimal("0.20")),
        SensitivityResult("c", Decimal("0.04"), Decimal("0.10")),
        SensitivityResult("d", Decimal("0.08"), Decimal("0.07")),
    )
    summary = summarize_results(results)
    assert summary.case_count == 4
    assert summary.min_return == Decimal("-0.02")
    assert summary.max_drawdown == Decimal("0.20")
    assert summary.median_return == Decimal("0.06")
    assert summary.positive_return_fraction == Decimal("0.75")
