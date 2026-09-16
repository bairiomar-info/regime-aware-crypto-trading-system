"""Explicit long-only spot compliance gate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpotComplianceConfig:
    forbidden_symbols: frozenset[str] = frozenset({"USDT", "USDC", "DAI"})

    def __post_init__(self) -> None:
        if not isinstance(self.forbidden_symbols, frozenset):
            raise TypeError("forbidden_symbols must be a frozenset")
        if any(not isinstance(symbol, str) or not symbol or symbol != symbol.upper() for symbol in self.forbidden_symbols):
            raise ValueError("forbidden_symbols must contain non-empty uppercase strings")


def validate_spot_symbol(symbol: str, config: SpotComplianceConfig = SpotComplianceConfig()) -> None:
    if not isinstance(symbol, str) or not symbol or symbol != symbol.upper():
        raise ValueError("symbol must be a non-empty uppercase string")
    if symbol in config.forbidden_symbols:
        raise ValueError(f"symbol is blocked by compliance policy: {symbol}")
