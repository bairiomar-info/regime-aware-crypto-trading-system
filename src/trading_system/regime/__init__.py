"""V1 multidimensional market-regime primitives."""

from .hysteresis import HysteresisConfig, HysteresisResult, HysteresisState, update_hysteresis
from .models import LevelState, MarketState, Transition, TrendState
from .state import evidence_confidence, transition_for
from .thresholds import classify_three_level, classify_trend, empirical_quantile

__all__ = [
    "HysteresisConfig",
    "HysteresisResult",
    "HysteresisState",
    "LevelState",
    "MarketState",
    "Transition",
    "TrendState",
    "classify_three_level",
    "classify_trend",
    "empirical_quantile",
    "evidence_confidence",
    "transition_for",
    "update_hysteresis",
]
