# Regime Dimension Ablation V1

Status: Research validation contract / implementation gate
Date: 2026-09-02

## Purpose

Determine whether the five V1 regime dimensions provide distinct, stable information before any dimension is allowed to receive trading authority.

The dimensions are:
- trend
- volatility
- breadth
- dispersion
- correlation

## Research basis

Ablation measures what changes when a component is withheld while the surrounding methodology is held fixed. Redundancy should be investigated separately from usefulness: correlated variables are not automatically useless, but overlapping information should not be counted as independent evidence.

Recent 2026 cryptocurrency research on cross-sectional dispersion reports information about later momentum deterioration even after controlling for Bitcoin volatility and average cross-asset correlation. This supports testing dimensions separately rather than assuming volatility, correlation, and dispersion are interchangeable.

Feature-selection literature distinguishes simple association, redundancy, and conditional/incremental relevance. These concepts must not be collapsed into one correlation threshold.

Multiple-testing research, including the Deflated Sharpe Ratio literature, shows that repeatedly searching alternatives and selecting favorable results creates selection bias. Therefore ablation variants are pre-registered and are not selected by historical trading performance.

## Pre-registered ablation variants

The first descriptive ablation set is fixed to:

1. trend only
2. trend + volatility
3. trend + breadth
4. trend + dispersion
5. trend + correlation
6. all five dimensions

No other combinations are added during this validation pass merely because they look favorable.

## What V1 measures

The first pass is observational, not a trading-performance test. For every variant, record:
- number of observations;
- number of complete observations;
- dimension coverage;
- classification/state signatures;
- agreement on dimensions shared with the full configuration;
- missingness and disagreement diagnostics.

These measurements establish whether removing a dimension materially changes the descriptive state representation.

## What V1 does not claim

A dimension changing the classification does not prove that it adds predictive value.

Likewise, a highly correlated dimension is not automatically removed. Incremental predictive value requires a later chronological test against a defined target/outcome, with realistic costs where trading decisions are evaluated.

## Methodological invariants

- No future observations.
- No strategy P&L used to choose an ablation variant.
- Same source data and time alignment across variants.
- Same classifier parameters unless a separately pre-registered experiment explicitly changes them.
- Missing observations remain missing; no imputation is introduced by ablation.
- Comparisons use only dimensions present in both configurations.
- Dimension names and ordering are deterministic.
- Ablation is diagnostic only and cannot alter live trading behavior.

## Relationship to redundancy analysis

Ablation answers: "What changes when this dimension is withheld?"

Redundancy analysis answers: "How dependent are the underlying measurements/classifications?"

Incremental-value testing answers: "Does the dimension improve a predefined out-of-sample objective after accounting for the other dimensions?"

These are separate questions and must remain separate in the research pipeline.

## Acceptance gate

The ablation layer is accepted when:
- the six pre-registered variants are deterministic;
- missingness is explicit;
- shared-dimension comparisons are well-defined;
- no ablation variant silently changes unrelated classifier parameters;
- results can be reproduced from the same inputs;
- and no variant is selected as "best" based on historical trading performance.

Only after this gate do we proceed to redundancy analysis and later chronological incremental-value testing.
