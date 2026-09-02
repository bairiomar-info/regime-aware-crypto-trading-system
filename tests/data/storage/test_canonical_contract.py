from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from trading_system.data.storage import (
    CanonicalizationContract,
    QualityClassification,
    QualityDiagnostic,
)


def test_default_contract_enforces_v1_invariants() -> None:
    contract = CanonicalizationContract(
        contract_version="1.0.0",
        schema_version="1.0.0",
        normalization_version="1.0.0",
        validation_version="1.0.0",
    )

    assert contract.numeric_representation == "decimal128"
    assert contract.timestamp_timezone == "UTC"
    assert contract.require_closed_candles is True
    assert contract.fabricate_missing_candles is False
    assert contract.reject_conflicting_duplicates is True


def test_contract_is_immutable() -> None:
    contract = CanonicalizationContract(
        contract_version="1.0.0",
        schema_version="1.0.0",
        normalization_version="1.0.0",
        validation_version="1.0.0",
    )

    with pytest.raises(ValidationError):
        contract.numeric_representation = "float64"


def test_contract_rejects_fabricated_candles() -> None:
    with pytest.raises(ValidationError, match="must not fabricate"):
        CanonicalizationContract(
            contract_version="1.0.0",
            schema_version="1.0.0",
            normalization_version="1.0.0",
            validation_version="1.0.0",
            fabricate_missing_candles=True,
        )


def test_contract_rejects_non_decimal128_v1_numeric_representation() -> None:
    with pytest.raises(ValidationError, match="decimal128"):
        CanonicalizationContract(
            contract_version="1.0.0",
            schema_version="1.0.0",
            normalization_version="1.0.0",
            validation_version="1.0.0",
            numeric_representation="float64",
        )


def test_contract_rejects_non_utc_timestamp_timezone() -> None:
    with pytest.raises(ValidationError, match="UTC"):
        CanonicalizationContract(
            contract_version="1.0.0",
            schema_version="1.0.0",
            normalization_version="1.0.0",
            validation_version="1.0.0",
            timestamp_timezone="Europe/Algiers",
        )


def test_quality_classification_values_are_stable() -> None:
    assert QualityClassification.VALID.value == "valid"
    assert QualityClassification.NO_TRADES.value == "no_trades"
    assert QualityClassification.DATA_GAP.value == "data_gap"
    assert QualityClassification.SOURCE_FAILURE.value == "source_failure"
    assert QualityClassification.HALT.value == "halt"
    assert QualityClassification.BREAK.value == "break"
    assert QualityClassification.UNKNOWN_GAP.value == "unknown_gap"
    assert QualityClassification.DUPLICATE.value == "duplicate"
    assert QualityClassification.DATA_CONFLICT.value == "data_conflict"


def test_quality_diagnostic_requires_utc_timestamp() -> None:
    diagnostic = QualityDiagnostic(
        classification=QualityClassification.DATA_GAP,
        observed_at=datetime(2026, 9, 2, 12, 0, tzinfo=UTC),
        message="Expected candle interval is absent.",
        symbol="BTCUSDT",
        timeframe="1h",
    )

    assert diagnostic.observed_at.tzinfo is UTC


def test_quality_diagnostic_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="UTC-aware"):
        QualityDiagnostic(
            classification=QualityClassification.DATA_GAP,
            observed_at=datetime(2026, 9, 2, 12, 0),
            message="Expected candle interval is absent.",
            symbol="BTCUSDT",
            timeframe="1h",
        )
