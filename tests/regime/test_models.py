from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from trading_system.regime.models import LevelState, MarketState, Transition, TrendState


def make_state(**overrides):
    values = dict(
        decision_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        trend=TrendState.UP,
        volatility=LevelState.NORMAL,
        breadth=LevelState.NORMAL,
        dispersion=LevelState.NORMAL,
        correlation=LevelState.NORMAL,
        transition=Transition.PERSISTING_UP,
        state_age=1,
        confidence=Decimal("0.5"),
    )
    values.update(overrides)
    return MarketState(**values)


def test_market_state_is_immutable() -> None:
    state = make_state()
    with pytest.raises(ValidationError):
        state.trend = TrendState.DOWN


def test_market_state_requires_utc_decision_time() -> None:
    with pytest.raises(ValidationError):
        make_state(decision_time=datetime(2026, 1, 1))


def test_confidence_is_bounded() -> None:
    for value in (Decimal("-0.01"), Decimal("1.01")):
        with pytest.raises(ValidationError):
            make_state(confidence=value)


def test_state_age_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        make_state(state_age=0)


def test_extra_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        make_state(unexpected="future-data")
