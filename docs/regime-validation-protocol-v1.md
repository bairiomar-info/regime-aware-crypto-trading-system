# Regime Validation Protocol V1

Status: Research validation contract / implementation gate
Date: 2026-09-02

## Purpose

Validate whether the V1 multidimensional regime layer adds reliable, causal, non-redundant information before it is allowed to influence strategy or portfolio decisions.

## Research conclusions

Recent cryptocurrency research supports regime dependence of momentum, especially persistent upward states, while transitions are materially weaker. Cross-sectional dispersion has recent evidence as a mechanism variable associated with later momentum deterioration even after controlling for Bitcoin volatility and average cross-asset correlation. These findings support testing regime dimensions as separate information channels rather than assuming one composite score is optimal.

Crypto momentum also exhibits severe tail and cross-sectional dependence. Therefore variance-only performance summaries are insufficient and validation must include drawdowns, tail outcomes, turnover/cost sensitivity, and out-of-sample stability.

Research using strict leakage controls shows that flexible models can overfit and fail after realistic costs. Our V1 should therefore remain deterministic and transparent and must pass causal, ablation, and walk-forward tests before any strategy integration.

## Validation layers

### 1. Causal integrity

For every decision time T:
- all reference observations are strictly earlier than T;
- the current decision observation is excluded from its own threshold reference distribution;
- finalized observations only;
- no future lifecycle, universe, or external-reference information;
- chronological state transitions only;
- repeated execution on identical inputs is deterministic.

A deliberately contaminated input must be detected or rejected by the surrounding data contract; the classifier must never silently infer that an unlabeled sequence element is historical.

### 2. Synthetic path tests

The classifier must behave sensibly under controlled paths:
- persistent UP;
- persistent DOWN;
- persistent neutral;
- gradual UP transition;
- gradual DOWN transition;
- abrupt crash;
- abrupt recovery;
- one-bar reversal;
- oscillation around entry boundaries;
- oscillation inside hysteresis bands;
- volatility spike without trend change;
- breadth deterioration without trend change;
- dispersion spike without trend change;
- correlation spike without trend change;
- temporary missing dimension;
- permanently insufficient history;
- degenerate reference distribution.

Expected behavior must be expressed as invariants, not hand-picked profitable outcomes.

### 3. Threshold sensitivity

Quantile windows and thresholds are configurable research parameters, not frozen optimal values. Validation must measure:
- state-frequency sensitivity;
- transition-frequency sensitivity;
- median and tail state duration;
- stability under small threshold perturbations;
- sensitivity to lookback length;
- sensitivity to confirmation length.

No parameter set may be selected because it maximizes historical trading performance on the same sample used to evaluate it.

### 4. Dimension ablation

Each dimension must be evaluated individually and in combinations:
- trend only;
- trend + volatility;
- trend + breadth;
- trend + dispersion;
- trend + correlation;
- all five dimensions.

The purpose is not to maximize a backtest metric immediately. The first question is whether each dimension changes regime classification in a stable, interpretable way and whether it adds information beyond dimensions already present.

### 5. Redundancy analysis

For the resulting time series of dimension measurements and classifications, measure dependence between dimensions. High dependence does not automatically justify deletion; it is evidence for testing incremental value rather than counting correlated dimensions multiple times.

Correlation is a risk/diversification variable and must not be treated as independent bullish/bearish evidence merely because it changes with market stress.

### 6. Walk-forward validation

Any numerical calibration must be chronological:
1. fit/calibrate using the past training window;
2. freeze parameters;
3. evaluate on the next unseen interval;
4. roll forward;
5. aggregate results across folds.

No full-sample threshold calibration is permitted for an out-of-sample claim.

### 7. Regime stability

Record:
- state duration distribution;
- transition counts;
- fraction of time in each state;
- fraction of time with insufficient state;
- number of rapid flips;
- dimension disagreement frequency;
- confidence distribution.

There is no predetermined ideal state-frequency distribution. Extreme concentration or excessive switching is a diagnostic requiring investigation.

### 8. Strategy-value test

Only after classifier validation passes, compare a simple baseline strategy with and without regime information. Required comparisons include:
- gross returns;
- net returns after realistic spot fees and turnover costs;
- drawdown;
- downside/tail statistics;
- turnover;
- exposure/cash time;
- performance by chronological test period;
- performance by regime state and transition.

The regime layer must earn its complexity through incremental out-of-sample value. A regime classifier that merely describes the market but does not improve risk-adjusted or implementation-adjusted decisions should not automatically control trading.

## Non-goals

V1 validation does not introduce HMMs, machine learning, sentiment, Google Trends, on-chain data, funding, derivatives, leverage, shorting, or discretionary overrides.

## Acceptance gate

The regime layer may influence strategy research only when:
- causal integrity tests pass;
- synthetic-path invariants pass;
- hysteresis/persistence behavior is stable;
- threshold sensitivity has been measured;
- dimension redundancy and ablation have been measured;
- chronological walk-forward calibration is demonstrated;
- regime statistics are documented;
- and a simple baseline comparison shows whether regime information adds incremental value after realistic costs.

Until then, the regime classifier remains an observational research component and must not control live trading.
