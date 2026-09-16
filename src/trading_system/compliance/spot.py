"""Explicit long-only spot compliance gate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpotComplianceConfig:
    forbidden_symbols: frozenset[str] = frozenset({"USDT", "USDC", "DAI"})


def validate_spot_symbol(symbol: str, config: SpotComplianceConfig = SpotComplianceConfig()) -> None:
    if not symbol or symbol != symbol.upper():
        raise ValueError("symbol must be non-empty uppercase")
    if symbol in config.forbidden_symbols:
        raise ValueError(f"symbol is blocked by compliance policy: {symbol}")
