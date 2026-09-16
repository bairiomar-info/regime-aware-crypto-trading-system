# Feature Engine V1

**Status:** Implementation contract / research baseline

## Purpose

The feature engine converts finalized, aligned spot OHLCV candles into causal market measurements consumed by the V1 regime classifier. It does not place orders, select assets, optimize parameters, or interpret a regime as bullish or bearish.

## Causality

The engine only reads candles supplied by the caller and never fetches or inspects observations after the final supplied candle. Inputs must be finalized and chronological. Cross-sectional features require timestamp alignment across the participating assets over the full feature window.

## V1 measurements

For each decision time the engine exposes:

- **trend_score:** mean per-asset cumulative log return over the configured trend window, normalized by the root-sum-square of returns. This is a directional persistence measurement, not a trading signal.
- **realized_volatility:** mean per-asset root-sum-square of log returns over the volatility window. Averaging per asset prevents the absolute scale from changing merely because the universe contains more assets.
- **breadth:** fraction of participating assets with a positive latest one-period log return.
- **cross_sectional_dispersion:** population standard deviation of latest one-period log returns across participating assets.
- **average_pairwise_correlation:** arithmetic mean of Pearson correlations between participating assets over the correlation window. If any pair has zero return variance, correlation is undefined and the aggregate is returned as unavailable rather than fabricating a zero.

These formulas are deliberately simple V1 research baselines. No parameter is declared optimal. They must be evaluated through the project's later walk-forward and robustness protocols.

## Input contract

All participating candles must:

- be finalized (`is_closed=True`)
- use UTC timestamps
- be strictly chronological within each asset
- use one timeframe per asset
- end at the same candle across assets
- use the same quote asset
- have enough observations for the largest configured lookback plus one price observation

If fewer than `min_assets` assets have enough history, the snapshot is returned with all feature values unavailable rather than imputed.

## Missing data

The engine does not fill gaps, interpolate prices, or manufacture returns. Misaligned histories are rejected. This keeps downstream regime classification explicit about data sufficiency.

## Numerical behavior

Log returns require positive close prices. Pearson correlation is undefined for a zero-variance series; the feature is therefore marked unavailable rather than treating undefined correlation as zero.

## Research boundary

The engine is intentionally separate from the classifier. The classifier remains responsible for empirical thresholds, threshold hysteresis, persistence confirmation, transitions, state age, and confidence evidence. The feature engine supplies measurements only.
