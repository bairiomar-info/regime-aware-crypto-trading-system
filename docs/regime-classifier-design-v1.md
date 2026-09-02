# Regime Classifier Design V1

**Status:** Implementation contract / research gate
**Date:** 2026-09-02

## Purpose

Define the causal, deterministic classifier that converts already-computed historical measurements into a point-in-time multidimensional `MarketState`.

The classifier is descriptive. It must not place orders, select assets, or contain strategy logic.

## Causality invariant

For decision time `T`, every quantity used by the classifier must be computable from observations available at or before `T`.

Adaptive thresholds are calculated from a historical reference window ending strictly before the observation being classified. The current observation is never included in its own threshold reference distribution.

## Inputs

The classifier receives one current measurement and one past-only reference window for each dimension:

- trend score
- realized volatility
- breadth
- cross-sectional dispersion
- average pairwise correlation

The caller is responsible for supplying PIT-eligible, finalized observations in chronological order. The classifier never fetches data and never repairs missing observations.

## Dimension states

Trend:

- `DOWN`
- `NEUTRAL`
- `UP`

Level dimensions:

- `LOW`
- `NORMAL`
- `HIGH`

Each dimension is classified independently. There is no weighted composite score.

## Adaptive thresholds

Each dimension uses configurable empirical quantiles from its past-only reference window.

The implementation must validate:

- quantiles are within `[0, 1]`
- lower threshold is strictly below upper threshold
- reference history meets the configured minimum observation count

Insufficient reference history produces an explicit unavailable result rather than a fabricated state.

No numerical quantile or lookback is declared optimal in V1. These remain research parameters for later walk-forward evaluation.

## Hysteresis and persistence

A dimension has two concepts:

1. threshold classification, which identifies the state supported by the current observation;
2. temporal stabilization, which decides whether that candidate becomes the accepted state.

A candidate different from the accepted state must satisfy the configured confirmation requirement before acceptance.

The accepted state and candidate state are retained separately. Repeated accepted-state observations clear the candidate and increase `state_age`.

The first valid observation initializes the accepted state and has `state_age = 1`.

## State history

The classifier processes observations sequentially. It never examines future states to determine the current state.

For each decision time it records:

- accepted dimension states
- transition of the directional trend state
- state age
- confidence metadata

## Transition semantics

The transition function receives `(current, previous)` and uses the frozen vocabulary:

- `UP, UP` → `PERSISTING_UP`
- `NEUTRAL, NEUTRAL` → `PERSISTING_NEUTRAL`
- `DOWN, DOWN` → `PERSISTING_DOWN`
- `UP, NEUTRAL` → `NEUTRAL_TO_UP`
- `UP, DOWN` → `DOWN_TO_UP`
- `NEUTRAL, UP` → `UP_TO_NEUTRAL`
- `NEUTRAL, DOWN` → `DOWN_TO_NEUTRAL`
- `DOWN, UP` → `UP_TO_DOWN`
- `DOWN, NEUTRAL` → `NEUTRAL_TO_DOWN`

The first valid state is treated as a persistence state because no previous observation exists.

## State age

V1 `state_age` counts consecutive accepted observations of the current **directional trend state**.

A candidate that has not yet been accepted does not reset the accepted state's age.

When a new trend state is accepted, age resets to `1`.

## Missing data

Missing current measurements are not imputed.

A dimension without sufficient current/reference data is unavailable. The classifier must not silently substitute a default state.

The V1 `MarketState` contract currently requires all five dimensions, so a complete market state can only be emitted when all five dimension classifications are available.

Partial dimension results may be represented by lower-level classifier results but must not be silently promoted to a complete `MarketState`.

## Confidence

V1 confidence is **evidence coherence**, not a probability and not a trading score.

The classifier must not manufacture confidence by averaging incomparable categorical states. Instead, the implementation will expose explicit dimension-level evidence/agreement inputs and aggregate those flags deterministically.

Until a scientifically justified directional-agreement mapping is researched, confidence must not be used to infer that `HIGH` volatility is bullish/bearish or that a particular combination is inherently supportive.

This deliberately separates classification from interpretation.

## Determinism

Given identical:

- current measurements
- historical reference windows
- configuration
- previous classifier state

output must be identical.

Mapping iteration order must never affect the result.

## V1 exclusions

The classifier does not include:

- HMM
- GARCH
- machine learning
- sentiment
- social data
- Google Trends
- on-chain signals
- funding rates
- stablecoin regime logic
- trading entries/exits
- portfolio weights
- execution logic

## Testing contract

Tests must cover:

1. strict past-only threshold windows
2. insufficient history
3. each dimension's state boundaries
4. first-state initialization
5. persistence
6. candidate rejection/reset
7. accepted-state age
8. every transition direction
9. missing dimensions
10. deterministic repeated execution
11. mapping-order independence
12. immutable `MarketState`
13. no future observation access

## Research rationale

Recent cryptocurrency evidence finds momentum is concentrated in persistent UP–UP states and weakened by state transitions, supporting explicit transition representation rather than a static bull/bear label. Recent work also finds lagged cross-sectional dispersion particularly informative about subsequent momentum breakdown, supporting its role as a separate state dimension rather than collapsing it into generic volatility.

The implementation therefore preserves the multidimensional state and transition information for later strategy research instead of prematurely converting it into a single opaque regime score.
