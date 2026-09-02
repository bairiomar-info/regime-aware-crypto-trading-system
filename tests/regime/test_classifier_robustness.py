from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading_system.regime import (
    DimensionConfig,
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


def test_gradual_trend_transition_requires_confirmation():
    history = _history()
    first = _run(_current(), history, confirm=2)
    candidate = _current("100")
    second = _run(candidate, history, first.classifier_state, offset=1, confirm=2)
    third = _run(candidate, history, second.classifier_state, offset=2, confirm=2)

    assert first.market_state.trend is TrendState.NEUTRAL
    assert second.market_state.trend is TrendState.NEUTRAL
    assert second.classifier_state.dimensions["trend"].candidate_state == "UP"
    assert third.market_state.trend is TrendState.UP
    assert third.market_state.transition is Transition.NEUTRAL_TO_UP


def test_abrupt_down_shock_requires_confirmation_without_lookahead():
    history = _history()
    first = _run(_current("100"), history, confirm=2)
    shock = _current("-100")

    second = _run(shock, history, first.classifier_state, offset=1, confirm=2)
    third = _run(shock, history, second.classifier_state, offset=2, confirm=2)

    assert second.market_state.trend is TrendState.UP
    assert second.classifier_state.dimensions["trend"].candidate_state == "DOWN"
    assert third.market_state.trend is TrendState.DOWN
    assert third.market_state.transition is Transition.UP_TO_DOWN
    assert third.market_state.state_age == 1


def test_recovery_before_confirmation_cancels_down_candidate():
    history = _history()
    first = _run(_current("100"), history, confirm=2)
    shock = _current("-100")
    second = _run(shock, history, first.classifier_state, offset=1, confirm=2)
    recovery = _current("100")
    third = _run(recovery, history, second.classifier_state, offset=2, confirm=2)

    assert third.market_state.trend is TrendState.UP
    assert third.classifier_state.dimensions["trend"].candidate_state is None
    assert third.classifier_state.dimensions["trend"].confirmation_count == 0


def test_temporary_missing_dimension_preserves_prior_trackers():
    history = _history()
    first = _run(_current(), history, confirm=2)
    missing = _current()
    missing["breadth"] = None
    second = _run(missing, history, first.classifier_state, offset=1, confirm=2)

    assert second.market_state is None
    assert second.classifier_state.dimensions["trend"].state == "NEUTRAL"
    assert second.classifier_state.dimensions["breadth"].state == "NEUTRAL"

    third = _run(_current(), history, second.classifier_state, offset=2, confirm=2)
    assert third.market_state is not None
    assert third.market_state.trend is TrendState.NEUTRAL
    assert third.market_state.state_age == 2


def test_non_monotonic_decision_time_is_rejected():
    history = _history()
    first = _run(_current(), history)
    with pytest.raises(ValueError, match="strictly after"):
        classify_market_state(
            T0,
            _current(),
            history,
            previous=first.classifier_state,
            config=_config(),
        )


def test_equal_quantile_reference_distribution_is_unavailable():
    history = {name: [Decimal("1")] * 20 for name in NAMES}
    result = _run(_current("1"), history)
    assert result.market_state is None
    assert all(item.state is None for item in result.dimensions)


def test_history_order_does_not_change_threshold_result():
    history = _history()
    reversed_history = {name: list(reversed(values)) for name, values in history.items()}
    left = _run(_current("100"), history)
    right = _run(_current("100"), reversed_history)
    assert left == right


def test_repeated_identical_path_is_deterministic():
    history = _history()
    currents = [_current("15"), _current("100"), _current("100"), _current("15")]

    states_a = []
    previous = None
    for offset, current in enumerate(currents):
        result = _run(current, history, previous, offset=offset, confirm=2)
        states_a.append(result)
        previous = result.classifier_state

    states_b = []
    previous = None
    for offset, current in enumerate(currents):
        result = _run(current, history, previous, offset=offset, confirm=2)
        states_b.append(result)
        previous = result.classifier_state

    assert states_a == states_b


def test_missing_history_dimension_does_not_fabricate_state():
    history = _history()
    history["correlation"] = []
    result = _run(_current(), history)
    assert result.market_state is None
    correlation = next(item for item in result.dimensions if item.dimension.value == "correlation")
    assert correlation.state is None
    assert correlation.sufficient_history is False


def test_current_extreme_does_not_modify_reference_thresholds():
    history = _history()
    baseline = _run(_current("15"), history)
    extreme_result = _run(_current("1000000"), history)
    baseline_repeat = _run(_current("15"), history)

    assert baseline.market_state == baseline_repeat.market_state
    assert baseline.classifier_state == baseline_repeat.classifier_state
    assert extreme_result.market_state.trend is TrendState.UP


def test_future_timestamp_in_previous_state_is_rejected():
    history = _history()
    first = _run(_current(), history)
    future_state = first.classifier_state.__class__(
        dimensions=first.classifier_state.dimensions,
        previous_trend=first.classifier_state.previous_trend,
        state_age=first.classifier_state.state_age,
        last_decision_time=T0 + timedelta(days=2),
    )
    with pytest.raises(ValueError, match="strictly after"):
        classify_market_state(
            T0 + timedelta(days=1),
            _current(),
            history,
            previous=future_state,
            config=_config(),
        )
