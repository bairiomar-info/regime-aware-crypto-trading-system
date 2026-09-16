from decimal import Decimal

import pytest

from trading_system.compliance.classification import AssetCompliance, validate_asset_compliance


def test_compliant_asset_passes() -> None:
    validate_asset_compliance(AssetCompliance("BTCUSDT", Decimal("0.05")))


def test_interest_income_above_threshold_rejected() -> None:
    with pytest.raises(ValueError, match="interest-income"):
        validate_asset_compliance(AssetCompliance("BTCUSDT", Decimal("0.0501")))


def test_gambling_like_asset_rejected() -> None:
    with pytest.raises(ValueError, match="gambling-like"):
        validate_asset_compliance(AssetCompliance("BTCUSDT", Decimal("0"), gambling_like=True))
