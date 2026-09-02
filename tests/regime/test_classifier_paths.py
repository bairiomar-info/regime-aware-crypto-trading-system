from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.regime import (
    DimensionConfig,
    LevelState,
    RegimeClassifierConfig,
    TrendState,
    Transition,
    classify_market_state,
)

NAMES = ("trend", "volatility", "breadth", "dispersion", "correlation")
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _config(confirm=2):
    dimension = DimensionConfig(min_observations=10, confirmation_bars=confirm)
    return RegimeClassifierConfig(
        trend=dimension,
        volatility=dimension,
        breadth=dimension,
        dispersion=dimension,
        correlation=dimension,
    )


def _history(size=30):
    values = [Decimal(i) for i in range(size)]
    return {name: values for name in NAMES}


def _current(value="15"):
    return {name: value for name in NAMES}


def _run(current, history, previous=None, offset=0, confirm=2):
    return classify_market_state(
        T0 + timedelta(hours=offset),
        current,
        history,
        previous=previous,
        config=_config(confirm),
    )


def test_persistent_up_remains_up_without_spurious_transition():
    history = _history()
    previous = None
    results = []
    for offset in range(5):
        result = _run(_current("100"), history, previous, offset=offset)
        results.append(result.market_state)
        previous = result.classifier_state

    assert all(state is not None and state.trend is TrendState.UP for state in results)
    assert results[0].transition is Transition.PERSISTING_UP
    assert results[-1].transition is Transition.PERSISTING_UP
    assert results[-1].state_age == 5


def test_persistent_down_remains_down_without_spurious_transition():
    history = _history()
    previous = None
    results = []
    for offset in range(5):
        result = _run(_current("-100"), history, previous, offset=offset)
        results.append(result.market_state)
        previous = result.classifier_state

    assert all(state is not None and state.trend is TrendState.DOWN for state in results)
    assert results[0].transition is Transition.PERSISTING_DOWN
    assert results[-1].transition is Transition.PERSISTING_DOWN
    assert results[-1].state_age == 5


def test_persistent_neutral_remains_neutral():
    history = _history()
    previous = None
    for offset in range(4):
        result = _run(_current("15"), history, previous, offset=offset)
        assert result.market_state is not None
        assert result.market_state.trend is TrendState.NEUTRAL
        assert result.market_state.transition is Transition.PERSISTING_NEUTRAL
        previous = result.classifier_state


def test_one_bar_reversal_does_not_create_direction_change():
    history = _history()
    first = _run(_current("100"), history)
    reversal = _run(_current("-100"), history, first.classifier_state, offset=1)
    recovery = _run(_current("100"), history, reversal.classifier_state, offset=2)

    assert first.market_state.trend is TrendState.UP
    assert reversal.market_state.trend is TrendState.UP
    assert recovery.market_state.trend is TrendState.UP
    assert recovery.classifier_state.dimensions["trend"].candidate_state is None


def test_oscillation_inside_hysteresis_band_does_not_flip_state():
    history = _history()
    first = _run(_current("100"), history)
    previous = first.classifier_state

    for offset, value in enumerate(("18", "19", "17", "19"), start=1):
        result = _run(_current(value), history, previous, offset=offset)
        assert result.market_state is not None
        assert result.market_state.trend is TrendState.UP
        previous = result.classifier_state


def test_non_trend_dimension_changes_do_not_change_trend_by_themselves():
    history = _history()
    first = _run(_current("15"), history)
    changed = _current("15")
    changed["volatility"] = "100000"
    changed["breadth"] = "-100000"
    changed["dispersion"] = "100000"
    changed["correlation"] = "100000"
    second = _run(changed, history, first.classifier_state, offset=1)

    assert first.market_state.trend is TrendState.NEUTRAL
    assert second.market_state.trend is TrendState.NEUTRAL
    assert second.market_state.volatility is LevelState.HIGH
    assert second.market_state.breadth is LevelState.LOW
    assert second.market_state.dispersion is LevelState.HIGH
    assert second.market_state.correlation is LevelState.HIGH


def test_missing_dimension_blocks_market_state_but_preserves_other_states():
    history = _history()
    first = _run(_current("100"), history)
    missing = _current("100")
    missing["dispersion"] = None
    second = _run(missing, history, first.classifier_state, offset=1)

    assert second.market_state is None
    assert second.classifier_state.dimensions["trend"].state == "UP"
    assert second.classifier_state.dimensions["volatility"].state == "HIGH"
    assert second.classifier_state.dimensions["dispersion"].state == "HIGH"

    third = _run(_current("100"), history, second.classifier_state, offset=2)
    assert third.market_state is not None
    assert third.market_state.trend is TrendState.UP


def test_non_monotonic_path_is_rejected_even_when_values_are_valid():
    history = _history()
    first = _run(_current("15"), history)
    with pytest.raises(ValueError, match="strictly after"):
        classify_market_state(
            T0,
            _current("15"),
            history,
            previous=first.classifier_state,
            config=_config(),
        )


def test_current_observation_does_not_change_reference_distribution():
    history = _history()
    ordinary = _run(_current("15"), history)
    extreme = _run(_current("1000000000"), history)
    ordinary_again = _run(_current("15"), history)

    assert ordinary.market_state == ordinary_again.market_state
    assert ordinary.classifier_state == ordinary_again.classifier_state
    assert extreme.market_state.trend is TrendState.UP


def test_configuration_changes_are_explicit_and_deterministic():
    history = _history()
    loose = _run(_current("100"), history, confirm=1)
    strict = _run(_current("100"), history, confirm=3)

    assert loose.market_state.trend is TrendState.UP
    assert strict.market_state.trend is TrendState.NEUTRAL
    assert strict.classifier_state.dimensions["trend"].candidate_state == "UP"
