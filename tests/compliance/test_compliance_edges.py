from decimal import Decimal

import pytest

from trading_system.compliance.classification import AssetCompliance, validate_asset_compliance
from trading_system.compliance.spot import SpotComplianceConfig, validate_spot_symbol


@pytest.mark.parametrize("ratio", [Decimal("0"), Decimal("0.01"), Decimal("0.049999"), Decimal("0.05")])
def test_interest_income_at_or_below_threshold_passes(ratio: Decimal) -> None:
    validate_asset_compliance(AssetCompliance("BTCUSDT", ratio))


@pytest.mark.parametrize("ratio", [Decimal("-0.01"), Decimal("1.01"), Decimal("NaN"), Decimal("Infinity")])
def test_interest_income_ratio_must_be_finite_unit_interval(ratio: Decimal) -> None:
    with pytest.raises(ValueError, match="interest_income_ratio"):
        AssetCompliance("BTCUSDT", ratio)


@pytest.mark.parametrize("symbol", ["", "btcusdt", "BTCUSDT "])
def test_asset_compliance_symbol_is_canonical(symbol: str) -> None:
    with pytest.raises(ValueError, match="symbol"):
        AssetCompliance(symbol, Decimal("0"))


def test_non_boolean_gambling_flag_rejected() -> None:
    with pytest.raises(TypeError, match="gambling_like"):
        AssetCompliance("BTCUSDT", Decimal("0"), gambling_like=1)  # type: ignore[arg-type]


def test_gambling_like_flag_blocks_even_zero_interest_income() -> None:
    with pytest.raises(ValueError, match="gambling-like"):
        validate_asset_compliance(AssetCompliance("BTCUSDT", Decimal("0"), gambling_like=True))


@pytest.mark.parametrize("symbol", ["USDT", "USDC", "DAI"])
def test_default_forbidden_symbols_are_blocked(symbol: str) -> None:
    with pytest.raises(ValueError, match="blocked"):
        validate_spot_symbol(symbol)


@pytest.mark.parametrize("symbol", ["", "btcusdt", "BTCUSDT "])
def test_spot_symbol_requires_uppercase_non_empty_identifier(symbol: str) -> None:
    with pytest.raises(ValueError, match="symbol"):
        validate_spot_symbol(symbol)


def test_custom_forbidden_symbol_policy_is_supported() -> None:
    config = SpotComplianceConfig(frozenset({"SCAMTOKEN"}))
    with pytest.raises(ValueError, match="blocked"):
        validate_spot_symbol("SCAMTOKEN", config)
    validate_spot_symbol("BTCUSDT", config)


def test_spot_config_requires_frozenset() -> None:
    with pytest.raises(TypeError, match="frozenset"):
        SpotComplianceConfig(set())  # type: ignore[arg-type]


def test_spot_config_rejects_noncanonical_symbols() -> None:
    with pytest.raises(ValueError, match="uppercase"):
        SpotComplianceConfig(frozenset({"usdt"}))
