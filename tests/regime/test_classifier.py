from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_system.regime import DimensionConfig, RegimeClassifierConfig, classify_market_state
from trading_system.regime.classifier import RegimeClassifierState
from trading_system.regime.models import LevelState, Transition, TrendState

NAMES = ("trend", "volatility", "breadth", "dispersion", "correlation")


def data(size=30):
    values = [Decimal(i) for i in range(size)]
    return ({name: "15" for name in NAMES}, {name: values for name in NAMES})


def config(confirm=2):
    d = DimensionConfig(min_observations=5, confirmation_bars=confirm)
    return RegimeClassifierConfig(trend=d, volatility=d, breadth=d, dispersion=d, correlation=d)


def test_complete_state():
    current, history = data()
    result = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), current, history, config=config())
    assert result.market_state is not None
    assert result.market_state.trend is TrendState.NEUTRAL
    assert result.market_state.volatility is LevelState.NORMAL
    assert result.market_state.transition is Transition.PERSISTING_NEUTRAL
    assert result.market_state.state_age == 1


def test_threshold_hysteresis_holds_up_state_inside_exit_band():
    current, history = data()
    cfg = config(confirm=1)
    first_current = dict(current)
    first_current["trend"] = "100"
    first = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), first_current, history, config=cfg)
    assert first.market_state is not None
    assert first.market_state.trend is TrendState.UP

    held_current = dict(current)
    held_current["trend"] = "18"
    held = classify_market_state(
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        held_current,
        history,
        previous=first.classifier_state,
        config=cfg,
    )
    assert held.market_state is not None
    assert held.market_state.trend is TrendState.UP
    assert held.classifier_state.dimensions["trend"].candidate_state is None


def test_threshold_hysteresis_allows_exit_then_confirmation():
    current, history = data()
    cfg = config(confirm=2)
    first_current = dict(current)
    first_current["trend"] = "100"
    first = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), first_current, history, config=cfg)
    assert first.market_state is not None
    assert first.market_state.trend is TrendState.UP

    exit_current = dict(current)
    exit_current["trend"] = "10"
    second = classify_market_state(
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        exit_current,
        history,
        previous=first.classifier_state,
        config=cfg,
    )
    assert second.market_state is not None
    assert second.market_state.trend is TrendState.UP
    assert second.classifier_state.dimensions["trend"].candidate_state == "NEUTRAL"
    assert second.classifier_state.dimensions["trend"].confirmation_count == 1

    third = classify_market_state(
        datetime(2026, 1, 3, tzinfo=timezone.utc),
        exit_current,
        history,
        previous=second.classifier_state,
        config=cfg,
    )
    assert third.market_state is not None
    assert third.market_state.trend is TrendState.NEUTRAL
    assert third.market_state.transition is Transition.UP_TO_NEUTRAL
    assert third.market_state.state_age == 1


def test_candidate_reversal_clears_pending_switch():
    current, history = data()
    cfg = config(confirm=2)
    first_current = dict(current)
    first_current["trend"] = "100"
    first = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), first_current, history, config=cfg)
    exit_current = dict(current)
    exit_current["trend"] = "10"
    second = classify_market_state(
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        exit_current,
        history,
        previous=first.classifier_state,
        config=cfg,
    )
    assert second.classifier_state.dimensions["trend"].confirmation_count == 1

    reversal = classify_market_state(
        datetime(2026, 1, 3, tzinfo=timezone.utc),
        first_current,
        history,
        previous=second.classifier_state,
        config=cfg,
    )
    assert reversal.market_state is not None
    assert reversal.market_state.trend is TrendState.UP
    assert reversal.classifier_state.dimensions["trend"].candidate_state is None
    assert reversal.classifier_state.dimensions["trend"].confirmation_count == 0


def test_insufficient_history():
    current, history = data(4)
    result = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), current, history, config=config())
    assert result.market_state is None
    assert all(not item.sufficient_history for item in result.dimensions)


def test_missing_dimension_is_unavailable():
    current, history = data()
    current["breadth"] = None
    result = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), current, history, config=config())
    assert result.market_state is None


def test_missing_dimension_preserves_other_trackers():
    current, history = data()
    cfg = config(confirm=2)
    first_current = dict(current)
    first_current["trend"] = "100"
    first = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), first_current, history, config=cfg)

    partial = dict(current)
    partial["trend"] = "10"
    partial["breadth"] = None
    second = classify_market_state(
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        partial,
        history,
        previous=first.classifier_state,
        config=cfg,
    )
    assert second.market_state is None
    assert second.classifier_state.dimensions["trend"].candidate_state == "NEUTRAL"

    third = classify_market_state(
        datetime(2026, 1, 3, tzinfo=timezone.utc),
        partial | {"breadth": "15"},
        history,
        previous=second.classifier_state,
        config=cfg,
    )
    assert third.market_state is not None
    assert third.market_state.trend is TrendState.NEUTRAL


def test_decision_time_must_advance():
    current, history = data()
    first = classify_market_state(datetime(2026, 1, 2, tzinfo=timezone.utc), current, history, config=config())
    with pytest.raises(ValueError, match="strictly after"):
        classify_market_state(
            datetime(2026, 1, 2, tzinfo=timezone.utc),
            current,
            history,
            previous=first.classifier_state,
            config=config(),
        )
    with pytest.raises(ValueError, match="strictly after"):
        classify_market_state(
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            current,
            history,
            previous=first.classifier_state,
            config=config(),
        )


def test_classifier_state_mapping_is_immutable():
    current, history = data()
    result = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), current, history, config=config())
    state = result.classifier_state
    with pytest.raises(TypeError):
        state.dimensions["trend"] = state.dimensions["trend"]


def test_classifier_state_rejects_naive_last_decision_time():
    with pytest.raises(ValueError, match="UTC"):
        RegimeClassifierState(last_decision_time=datetime(2026, 1, 1))


def test_order_independent_and_utc_required():
    current, history = data()
    a = classify_market_state(datetime(2026, 1, 1, tzinfo=timezone.utc), current, history, config=config())
    b = classify_market_state(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        dict(reversed(list(current.items()))),
        dict(reversed(list(history.items()))),
        config=config(),
    )
    assert a == b
    try:
        classify_market_state(datetime(2026, 1, 1), current, history, config=config())
    except ValueError:
        pass
    else:
        raise AssertionError("UTC validation expected")


def test_explicit_evidence_controls_confidence():
    current, history = data()
    result = classify_market_state(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        current,
        history,
        config=config(),
        evidence=[True, None, True],
    )
    assert result.market_state is not None
    assert result.market_state.confidence == Decimal("1")
