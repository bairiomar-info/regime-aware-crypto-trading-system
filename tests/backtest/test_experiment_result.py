from datetime import datetime, timezone
from decimal import Decimal

from trading_system.backtest.alpha_evidence import AlphaEvidence
from trading_system.backtest.alpha_gate import AlphaGateResult
from trading_system.backtest.experiment_manifest import ExperimentManifest
from trading_system.backtest.experiment_result import (
    bind_result_to_manifest,
    fingerprint_experiment_result,
    serialize_experiment_result,
)


def _evidence() -> AlphaEvidence:
    return AlphaEvidence(
        gate=AlphaGateResult(True, True, True, True),
        regimes=(),
        oos_window_count=2,
        worst_oos_return=Decimal("0.01"),
        worst_regime_return=Decimal("0.02"),
        all_oos_windows_positive=True,
        all_regimes_positive=True,
    )


def _manifest() -> ExperimentManifest:
    return ExperimentManifest(
        experiment_id="exp-001",
        dataset_id="btc-1h",
        strategy_id="momentum-v1",
        started_at=datetime(2026, 9, 16, tzinfo=timezone.utc),
        parameters=(("lookback", "24"),),
        cost_model_id="spot-fee-v1",
        walk_forward_id="wf-v1",
    )


def test_result_binds_to_manifest_and_serializes_deterministically() -> None:
    result = bind_result_to_manifest(_manifest(), _evidence())
    first = serialize_experiment_result(result)
    second = serialize_experiment_result(result)
    assert first == second
    assert result.manifest_fingerprint == _manifest().fingerprint()
    assert fingerprint_experiment_result(result) == fingerprint_experiment_result(result)
