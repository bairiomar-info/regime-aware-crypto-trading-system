from decimal import Decimal

import pytest

from trading_system.backtest.alpha_gate import AlphaGateConfig
from trading_system.backtest.oos_evidence import evaluate_oos_alpha_evidence
from trading_system.backtest.oos_experiments import OOSExperimentResult
from trading_system.backtest.evaluation import OOSWindowResult
from trading_system.backtest.regime_stability import RegimeOOSResult


def _experiment(returns: tuple[str, ...]) -> OOSExperimentResult:
    windows = tuple(
        OOSWindowResult(
            window_index=index,
            total_return=Decimal(value),
            max_drawdown=Decimal("0"),
        )
        for index, value in enumerate(returns)
    )
    return OOSExperimentResult(case_name="case", windows=windows, compounded_return=Decimal("0"), worst_drawdown=Decimal("0"))


def test_oos_evidence_requires_consistent_window_counts() -> None:
    regime = RegimeOOSResult(regime="bull", windows=(), worst_return=Decimal("0.01"))
    with pytest.raises(ValueError, match="same OOS window count"):
        evaluate_oos_alpha_evidence(
            summary=None,  # type: ignore[arg-type]
            experiments=(_experiment(("0.01",)), _experiment(("0.01", "0.02"))),
            regimes=(regime,),
        )
