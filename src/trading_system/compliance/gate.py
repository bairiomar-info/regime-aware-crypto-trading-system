"""Compliance gate for research trade candidates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ComplianceDecision(StrEnum):
    ALLOW = "ALLOW"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class ComplianceResult:
    decision: ComplianceDecision
    reason: str

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("reason must not be empty")


def evaluate_symbol(symbol: str, forbidden_symbols: frozenset[str]) -> ComplianceResult:
    """Apply the configured hard blocklist; unknown classifications remain reviewable."""
    if not symbol or symbol != symbol.upper():
        return ComplianceResult(ComplianceDecision.REJECT, "invalid_symbol")
    if symbol in forbidden_symbols:
        return ComplianceResult(ComplianceDecision.REJECT, "forbidden_symbol")
    return ComplianceResult(ComplianceDecision.REVIEW, "classification_required")
