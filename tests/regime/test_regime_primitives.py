from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.regime import (
    HysteresisConfig,
    HysteresisState,
    LevelState,
    MarketState,
    Transition,
    TrendState,
    classify_three_level,
    classify_trend,
    empirical_quantile,
    evidence_confidence,
    transition_for,
    update_hysteresis,
)


def test_empirical_quantile_is_interpolated_and_empty_is_none():
    assert empirical_quantile(["1", "2", "3", "4"], "0.5") == Decimal("2.5")
    assert empirical_quantile([], "0.5") is None


def test_empirical_quantile_rejects_invalid_quantile():
    with pytest.raises(ValueError, match="between zero and one"):
        empirical_quantile(["1"], "1.1")


def test_three_level_classification_uses_strict_outer_boundaries():
    assert classify_three_level("1", low_entry="2", high_entry="4") == "LOW"
    assert classify_three_level("2", low_entry="2", high_entry="4") == "NORMAL"
    assert classify_three_level("4", low_entry="2", high_entry="4") == "NORMAL"
    assert classify_three_level("5", low_entry="2", high_entry="4") == "HIGH"
    assert classify_three_level(None, low_entry="2", high_entry="4") is None


def test_trend_classification():
    assert classify_trend("-2", down_entry="-1", up_entry="1") == "DOWN"
    assert classify_trend("0", down_entry="-1", up_entry="1") == "NEUTRAL"
    assert classify_trend("2", down_entry="-1", up_entry="1") == "UP"


def test_transition_mapping():
    assert transition_for(TrendState.UP, None) is Transition.PERSISTING_UP
    assert transition_for(TrendState.UP, TrendState.NEUTRAL) is Transition.NEUTRAL_TO_UP
    assert transition_for(TrendState.DOWN, TrendState.UP) is Transition.UP_TO_DOWN
    assert transition_for(TrendState.NEUTRAL, TrendState.DOWN) is Transition.DOWN_TO_NEUTRAL


def test_evidence_confidence_excludes_missing_items():
    assert evidence_confidence([True, True, False, None]) == Decimal("2") / Decimal("3")
    assert evidence_confidence([None, None]) == Decimal("0")


def test_hysteresis_requires_consecutive_confirmation():
    cfg = HysteresisConfig(confirmation_bars=2)
    first = update_hysteresis(None, "UP", config=cfg)
    assert first.state == "UP"
    second = update_hysteresis("UP", "DOWN", confirmation_count=0, state_age=3, config=cfg)
    assert second.state == "UP"
    assert second.candidate_state == "DOWN"
    assert second.confirmation_count == 1
    assert second.status is HysteresisState.CANDIDATE
    third = update_hysteresis("UP", "DOWN", confirmation_count=1, state_age=4, config=cfg)
    assert third.state == "DOWN"
    assert third.state_age == 1
    assert third.status is HysteresisState.ACCEPTED


def test_hysteresis_same_state_increments_age_and_clears_candidate():
    result = update_hysteresis("UP", "UP", confirmation_count=1, state_age=4)
    assert result.state == "UP"
    assert result.candidate_state is None
    assert result.confirmation_count == 0
    assert result.state_age == 5


def test_market_state_is_immutable_and_utc():
    state = MarketState(
        decision_time=datetime(2026, 9, 2, tzinfo=timezone.utc),
        trend=TrendState.UP,
        volatility=LevelState.NORMAL,
        breadth=LevelState.HIGH,
        dispersion=LevelState.LOW,
        correlation=LevelState.NORMAL,
        transition=Transition.PERSISTING_UP,
        state_age=3,
        confidence=Decimal("0.8"),
    )
    assert state.confidence == Decimal("0.8")
    with pytest.raises((TypeError, ValueError)):
        state.state_age = 4
