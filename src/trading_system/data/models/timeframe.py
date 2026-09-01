"""Canonical timeframe model."""

from enum import StrEnum


class Timeframe(StrEnum):
    """Timeframes supported by the initial research/data pipeline."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
