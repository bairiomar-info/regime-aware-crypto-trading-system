# Regime Redundancy Analysis V1

**Status:** Architecture/research contract frozen  
**Date:** 2026-09-02

## Purpose

Determine whether the five regime dimensions contain overlapping information without prematurely removing any dimension or using trading P&L as a selection criterion.

Dimensions:
- trend
- volatility
- breadth
- dispersion
- correlation

## Research principles

1. Redundancy is not the same as uselessness.
2. Measurement redundancy, state redundancy, and predictive redundancy are separate questions.
3. Descriptive redundancy analysis must not use future observations or future returns.
4. No dimension is removed from the architecture based on correlation alone.
5. Predictive usefulness is evaluated later through pre-registered causal ablation and walk-forward out-of-sample testing with realistic costs and multiple-testing controls.
6. Pairwise methods are preferred initially because only five dimensions exist; avoid PCA, graph optimization, DCC-GARCH, and other unnecessary machinery.

## V1 measurement redundancy

For aligned continuous measurement series, compute pairwise Spearman rank correlation.

Requirements:
- equal-length aligned windows;
- complete paired observations only;
- no imputation;
- minimum observation count is explicit/configurable;
- ties receive average ranks;
- constant ranked series produce an undefined (`None`) result;
- deterministic dimension ordering;
- report valid observation count with each result.

Spearman is preferred to Pearson because it captures monotonic dependence while reducing sensitivity to measurement scale and extreme values. This is consistent with feature-selection research that separates relevance, redundancy, and complementarity and uses rank correlation for pairwise association. [Tsanas, 2022](https://pubmed.ncbi.nlm.nih.gov/35607618/)

## V1 state redundancy

For already-classified regime states, compare exact state agreement for a pair or explicitly selected dimension subset.

Requirements:
- compare only rows where all selected states are present;
- report comparable count, agreement count, and agreement ratio;
- do not assign numerical distances to categorical states;
- do not infer causality or predictive value from agreement.

## Conditional/incremental redundancy

Conditional association is recognized as a separate research question. Rank partial correlation can quantify information that remains after conditioning on other variables, and feature-selection research explicitly distinguishes this complementarity from pairwise redundancy. [Tsanas, 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9122960/)

It is **not part of the first implementation** unless a concrete, stable measurement representation and conditioning protocol are established. We will not build a complex partial-correlation network merely because it is available in the literature.

## Interpretation guardrails

- High absolute Spearman correlation = evidence of measurement overlap, not automatic deletion.
- High state agreement = evidence of classification overlap, not proof of redundant predictive content.
- Low pairwise correlation = not proof of incremental trading value.
- A dimension can be correlated with another and still be complementary.
- Dispersion deserves particular attention because recent crypto evidence reports information about momentum breakdown after controlling for Bitcoin volatility and average cross-asset correlation. [Zhang & Makgolo, 2026](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6648082)

## Later predictive stage

Only after descriptive redundancy analysis:

1. pre-register predictive targets;
2. use point-in-time information only;
3. run the existing ablation variants;
4. compare incremental predictive value;
5. use walk-forward/out-of-sample evaluation;
6. include realistic transaction costs and turnover;
7. assess stability across folds/regimes;
8. account for multiple testing/selection bias;
9. only then consider KEEP / RESTRICT / REMOVE decisions.

This keeps the regime layer research-only until incremental value is demonstrated.
