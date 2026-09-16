from decimal import Decimal

import pytest

from trading_system.backtest.evaluation import OOSWindowResult
from trading_system.backtest.oos_experiments import OOSExperimentResult, run_oos_experiments


def _result(name: str, returns: tuple[str, ...]) -> OOSExperimentResult:
    windows = tuple(
        OOSWindowResult(
            window_index=i,
            total_return=Decimal(value),
            max_drawdown=Decimal("-0.01"),
        )
        for i, value in enumerate(returns)
    )
    return OOSExperimentResult(
        case_name=name,
        windows=windows,
        compounded_return=Decimal("0.10"),
        worst_drawdown=Decimal("-0.05"),
    )


def test_multiple_cases_and_windows_are_aggregated() -> None:
    cases = ("baseline", "variant")
    results = {
        "baseline": _result("baseline", ("0.01", "0.02", "0.03")),
        "variant": _result("variant", ("0.02", "-0.01", "0.04")),
    }

    def runner(case: str, index: int) -> OOSExperimentResult:
        result = results[case]
        window = result.windows[index]
        return OOSExperimentResult(
            case_name=case,
            windows=(window,),
            compounded_return=window.total_return,
            worst_drawdown=window.max_drawdown,
        )

    output = run_oos_experiments(cases, runner, 3)
    assert len(output) == 2
    assert [item.case_name for item in output] == ["baseline", "variant"]
    assert [len(item.windows) for item in output] == [3, 3]
    assert output[1].windows[1].total_return == Decimal("-0.01")


def test_empty_cases_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least one case"):
        run_oos_experiments((), lambda case, index: None, 1)  # type: ignore[arg-type]


def test_non_positive_window_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="window_count"):
        run_oos_experiments(("baseline",), lambda case, index: None, 0)  # type: ignore[arg-type]
