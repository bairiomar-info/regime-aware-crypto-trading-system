"""V1 multidimensional market-regime primitives."""

from .classifier import (
    Dimension,
    DimensionClassification,
    DimensionConfig,
    DimensionTracker,
    RegimeClassificationResult,
    RegimeClassifierConfig,
    RegimeClassifierState,
    classify_market_state,
)
from .hysteresis import HysteresisConfig, HysteresisResult, HysteresisState, update_hysteresis
from .models import LevelState, MarketState, Transition, TrendState
from .state import evidence_confidence, transition_for
from .thresholds import (
    classify_three_level,
    classify_three_level_hysteresis,
    classify_trend,
    classify_trend_hysteresis,
    empirical_quantile,
)

__all__ = [
    "Dimension",
    "DimensionClassification",
    "DimensionConfig",
    "DimensionTracker",
    "RegimeClassificationResult",
    "RegimeClassifierConfig",
    "RegimeClassifierState",
    "classify_market_state",
    "HysteresisConfig",
    "HysteresisResult",
    "HysteresisState",
    "LevelState",
    "MarketState",
    "Transition",
    "TrendState",
    "classify_three_level",
    "classify_three_level_hysteresis",
    "classify_trend",
    "classify_trend_hysteresis",
    "empirical_quantile",
    "evidence_confidence",
    "transition_for",
    "update_hysteresis",
]
