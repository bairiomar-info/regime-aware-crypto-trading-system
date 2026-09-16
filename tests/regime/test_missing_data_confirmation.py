from datetime import datetime, timezone

from trading_system.regime import DimensionConfig, RegimeClassifierConfig, classify_market_state
from trading_system.regime.models import TrendState

NAMES = ("trend", "volatility", "breadth", "dispersion", "correlation")


def _config() -> RegimeClassifierConfig:
    d = DimensionConfig(min_observations=5, confirmation_bars=2)
    return RegimeClassifierConfig(trend=d, volatility=d, breadth=d, dispersion=d, correlation=d)


def _data():
    return ({name: "15" for name in NAMES}, {name: [str(i) for i in range(30)] for name in NAMES})


def test_unavailable_dimension_cannot_bridge_confirmation_gap() -> None:
    current, history = _data()
    cfg = _config()

    first_current = dict(current)
    first_current["trend"] = "100"
    first = classify_market_state(
        datetime(2026, 1, 1, tzinfo=timezone.utc), first_current, history, config=cfg
    )
    assert first.market_state is not None
    assert first.market_state.trend is TrendState.UP

    exit_current = dict(current)
    exit_current["trend"] = "10"
    second = classify_market_state(
        datetime(2026, 1, 2, tzinfo=timezone.utc), exit_current, history, previous=first.classifier_state, config=cfg
    )
    assert second.classifier_state.dimensions["trend"].candidate_state == "NEUTRAL"
    assert second.classifier_state.dimensions["trend"].confirmation_count == 1

    unavailable = dict(exit_current)
    unavailable["trend"] = None
    third = classify_market_state(
        datetime(2026, 1, 3, tzinfo=timezone.utc), unavailable, history, previous=second.classifier_state, config=cfg
    )
    assert third.market_state is None
    assert third.classifier_state.dimensions["trend"].candidate_state is None
    assert third.classifier_state.dimensions["trend"].confirmation_count == 0

    fourth = classify_market_state(
        datetime(2026, 1, 4, tzinfo=timezone.utc), exit_current, history, previous=third.classifier_state, config=cfg
    )
    assert fourth.market_state is not None
    assert fourth.market_state.trend is TrendState.UP
    assert fourth.classifier_state.dimensions["trend"].candidate_state == "NEUTRAL"
    assert fourth.classifier_state.dimensions["trend"].confirmation_count == 1
