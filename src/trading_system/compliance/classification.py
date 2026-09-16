"""Explicit asset-level compliance evidence for hard pre-trade decisions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AssetCompliance:
    symbol: str
    interest_income_ratio: Decimal
    gambling_like: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be a non-empty uppercase string")
        if not isinstance(self.interest_income_ratio, Decimal) or not self.interest_income_ratio.is_finite() or not Decimal("0") <= self.interest_income_ratio <= Decimal("1"):
            raise ValueError("interest_income_ratio must be a finite Decimal within [0, 1]")
        if not isinstance(self.gambling_like, bool):
            raise TypeError("gambling_like must be a bool")


def validate_asset_compliance(asset: AssetCompliance) -> None:
    if asset.interest_income_ratio > Decimal("0.05"):
        raise ValueError("asset exceeds configured interest-income threshold")
    if asset.gambling_like:
        raise ValueError("asset is classified as gambling-like")
