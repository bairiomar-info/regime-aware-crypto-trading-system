# Regime Detection Specification v1

**Status:** Architecture freeze / implementation contract  
**Date:** 2026-09-02

## 1. Purpose

Define the V1 market-state layer for the research-driven, long-only spot trading system. The regime layer describes market conditions and supplies structured state information to strategy and risk layers. It does not place orders or contain buy/sell rules.

## 2. Core principles

- All regime observations are point-in-time (PIT).
- A decision at time `T` may use only information available at or before `T`.
- Current/incomplete candles are excluded unless explicitly modeled as incomplete observations; V1 uses finalized observations.
- Rolling statistics and thresholds are computed from historical information only.
- Missing observations are not silently imputed.
- Thresholds are configurable research parameters; no threshold is declared universally optimal.
- State changes require persistence/confirmation and hysteresis to reduce noise.
- Internal state remains multidimensional; V1 does not collapse all dimensions into one arbitrary weighted score.
- Confidence is an evidence-coherence measure in V1, not a calibrated probability.
- The regime layer must not generate trading orders.

## 3. State dimensions

### 3.1 Trend

States:
- `UP`
- `NEUTRAL`
- `DOWN`

Trend describes directional market conditions using the already-approved historical trend primitives.

### 3.2 Volatility

States:
- `LOW`
- `NORMAL`
- `HIGH`

Volatility is primarily a risk/intensity dimension. High volatility is not inherently bullish or bearish.

### 3.3 Breadth

States:
- `LOW`
- `NORMAL`
- `HIGH`

Breadth is computed from valid PIT-eligible/readiness-complete observations. Missing observations are excluded from the denominator rather than treated as negative observations.

### 3.4 Cross-sectional dispersion

States:
- `LOW`
- `NORMAL`
- `HIGH`

Dispersion represents disagreement/differentiation across the eligible cross-section. It is a market-state and momentum-reliability/risk input, not an automatic sell signal.

### 3.5 Correlation

States:
- `LOW`
- `NORMAL`
- `HIGH`

Correlation primarily describes diversification/contagion conditions. It is not a standalone directional trading signal.

## 4. Threshold methodology

V1 uses adaptive, historical thresholding rather than fixed universal numerical cutoffs.

Thresholds must be derived only from the historical information available at the decision time. Candidate methodologies may include rolling empirical quantiles or other explicitly documented robust historical estimators.

Threshold configuration must be versioned and exposed to experiments. Threshold windows and quantile values are research parameters and must not be presented as optimized until evaluated through the project's walk-forward validation process.

No global full-sample threshold fitting is permitted for an OOS decision.

## 5. Persistence and hysteresis

Regime classification must distinguish a temporary threshold crossing from a confirmed state change.

V1 therefore supports:
- candidate state
- confirmation/persistence evidence
- separate entry/exit boundaries where appropriate
- current state
- state age

The exact confirmation rule and numerical persistence requirement remain configurable research parameters. They must be evaluated for regime churn, detection delay, stability, and downstream portfolio impact before any value is considered preferred.

## 6. Multidimensional aggregation

The classifier preserves each dimension independently:

```text
Trend       -> UP / NEUTRAL / DOWN
Volatility  -> LOW / NORMAL / HIGH
Breadth     -> LOW / NORMAL / HIGH
Dispersion  -> LOW / NORMAL / HIGH
Correlation -> LOW / NORMAL / HIGH
```

The dimensions are combined into a structured market-state object, not an arbitrary weighted scalar score.

Aggregation may derive a coarse directional continuity state from the trend dimension and supporting evidence, but must retain all underlying dimensions for downstream research.

## 7. Transition model

V1 explicitly represents temporal transitions:

- `PERSISTING_UP`
- `PERSISTING_NEUTRAL`
- `PERSISTING_DOWN`
- `UP_TO_NEUTRAL`
- `UP_TO_DOWN`
- `NEUTRAL_TO_UP`
- `NEUTRAL_TO_DOWN`
- `DOWN_TO_NEUTRAL`
- `DOWN_TO_UP`

Transitions are calculated from the prior confirmed state and the current confirmed state. A transition must never be inferred using future observations.

## 8. State age

`state_age` records how long the current confirmed state has persisted according to the classifier's decision cadence.

A state age of zero/one must have an explicitly defined convention in implementation and tests. The convention must remain deterministic and PIT-safe.

## 9. Confidence

V1 confidence represents the coherence/quality of available evidence supporting the current structured state.

It may incorporate:
- agreement among valid state dimensions
- data sufficiency
- minimum cross-sectional breadth
- readiness completeness
- stability/persistence evidence

It must not be described as a probability of a future return or a probability that the current state is objectively true.

A future probabilistic regime model may introduce calibrated probabilities separately.

## 10. Data sufficiency

The classifier must expose whether the required inputs are sufficiently available.

Insufficient data must produce an explicit non-ready/insufficient result rather than silently substituting values.

Minimum cross-section requirements and lookback requirements are configurable and must be visible in the experiment configuration.

## 11. Temporal integrity contract

The required causal sequence is:

```text
DATA AVAILABLE
      -> FEATURES CALCULATED
      -> STATE CLASSIFIED
      -> SIGNAL CALCULATED
      -> ORDER GENERATED
      -> ORDER EXECUTED
```

No regime feature may use a future bar, future universe membership, future liquidity, future market capitalization, future delisting information, or a full-history smoothed latent-state estimate at the decision time.

## 12. Research parameters

The following remain intentionally configurable:

- feature lookback windows
- threshold estimation windows
- threshold quantiles
- neutral-band widths
- hysteresis widths
- persistence/confirmation requirements
- minimum valid observations
- state aggregation rules
- confidence calculation parameters

These parameters must be evaluated with walk-forward research and recorded as experiment configuration.

## 13. V1 exclusions

The initial regime layer does not require:

- sentiment
- Google Trends
- social-media signals
- funding rates
- derivatives positioning
- on-chain regime signals
- complex machine learning
- reinforcement learning
- HMM/GARCH as the primary classifier
- graph/network contagion models
- discretionary news interpretation

These remain candidates for later research only if they demonstrate incremental value under the project's validation framework.

## 14. Future probabilistic models

HMM and related regime-switching models are supported as future research. Existing literature demonstrates useful latent regime modeling in cryptocurrencies, but V1 deliberately prioritizes transparent, causal, testable state primitives. If an HMM is later evaluated, only information available at the decision time may influence the live/backtest state; full-history smoothing or Viterbi paths that use future observations are prohibited for causal signals.

## 15. Research rationale

Recent crypto research finds momentum strongly dependent on market-state continuity, with persistent UP-UP conditions particularly favorable and transitions suppressing momentum. Other research finds distinct regime behavior and persistence in crypto returns and volatility. These findings support explicit state transitions and persistence while not justifying an arbitrary universal threshold or a single monolithic regime label.

## 16. Acceptance criteria

Implementation is accepted only if tests demonstrate:

1. PIT-safe threshold calculation.
2. No future-data access.
3. Deterministic classification.
4. Correct three-way state classification for every dimension.
5. Explicit insufficient-data behavior.
6. Correct hysteresis/persistence behavior.
7. Correct transition labeling.
8. Correct state-age handling.
9. Confidence remains evidence coherence, not a probability.
10. Underlying dimensions remain inspectable.
11. Missing observations are not silently imputed.
12. No trading/execution behavior exists inside the regime layer.
13. Configuration is explicit and versionable.
14. Walk-forward research can vary regime parameters without modifying implementation logic.

## 17. Non-goals

This specification does not define:

- strategy entry/exit rules
- portfolio weights
- risk limits
- execution logic
- order management
- transaction-cost assumptions
- final optimal parameters

Those belong to subsequent research and architecture stages.
