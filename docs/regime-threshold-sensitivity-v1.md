# Regime Threshold Sensitivity V1

Status: Research validation contract / implementation gate
Date: 2026-09-02

## Purpose

Measure whether the V1 regime classifier behaves stably under small, pre-specified changes to its adaptive quantile thresholds, without selecting parameters by historical trading performance.

## Research basis

Backtest research consistently warns that searching many parameter combinations and reporting the best result creates selection bias and overfitting. The Deflated Sharpe Ratio was specifically developed to account for multiple testing and non-normal returns. Recent work also recommends examining the full parameter surface rather than relying on one selected optimum. Therefore this stage evaluates classifier behavior, not strategy profitability.

## Scope

Sensitivity analysis covers:

- lower and upper entry quantiles;
- lower and upper exit quantiles;
- reference lookback length;
- confirmation length.

The baseline is the current V1 configuration:

- entry quantiles: 0.33 / 0.67;
- exit quantiles: 0.40 / 0.60;
- confirmation bars: 2.

These are provisional research defaults, not optimized values.

## Perturbation policy

Use a small, explicitly defined neighborhood around the baseline. Variants must be generated before looking at trading performance. Every tested configuration is recorded.

The sensitivity layer must not:

- search an arbitrarily large grid;
- choose a configuration using historical returns;
- use future observations to form thresholds;
- modify the classifier's causal contract;
- silently discard unstable variants.

Invalid quantile orderings are rejected rather than repaired automatically.

## Measurements

For every configuration/path, record:

1. state frequency by trend and each categorical dimension;
2. transition frequency;
3. median accepted-state duration;
4. upper-tail accepted-state duration;
5. rapid-flip count;
6. fraction of missing/insufficient classifications;
7. agreement with the baseline classification sequence.

No universal target state-frequency distribution is assumed.

## Interpretation

A robust classifier should show a reasonably stable qualitative structure under small perturbations. Large changes in state occupancy, excessive transition creation, or large baseline disagreement are diagnostics for further investigation.

A sensitivity failure does not automatically mean the classifier is useless. It means that the current parameterization is not sufficiently stable to justify treating the output as a reliable structural state without additional research.

## Statistical discipline

This stage is descriptive and diagnostic. It does not produce an alpha claim.

When trading performance is eventually evaluated, the full search history and number of trials must be retained. Performance selection will require chronological out-of-sample validation and appropriate multiple-testing controls; a high in-sample result from one sensitivity variant is not an acceptance criterion.

## Causality

Threshold reference observations are supplied by the caller and must be strictly earlier than the decision time. The current observation is excluded from the reference distribution. The sensitivity layer never expands a historical window with future data.

## Acceptance gate

Threshold sensitivity is considered measured only when:

- baseline and all pre-registered variants are evaluated;
- state/transition/duration/missingness statistics are recorded;
- baseline agreement is measured;
- confirmation and lookback sensitivity are explicitly represented;
- no variant is selected on trading performance;
- all calculations are deterministic.

Passing this gate does not grant the regime layer trading authority. Dimension ablation remains next.
