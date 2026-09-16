# Regime-Aware Crypto Trading System

Research-driven, long-only spot quantitative crypto trading system.

## Current architecture

```text
Market data → causal features → multidimensional regimes → strategies → portfolio → risk → compliance → execution boundary → backtest/metrics
```

The repository is intentionally built in research gates. A layer must be deterministic, tested, and causality-safe before it is used by the next layer.

### Implemented

- Canonical UTC OHLCV market-data models
- Binance Spot historical acquisition and normalization
- Acquisition manifests and validation
- Causal multidimensional regime classifier
- Threshold hysteresis and persistence confirmation
- Regime transitions, state age, evidence confidence
- Regime sensitivity, ablation, redundancy, and robustness tooling
- Causal V1 market feature engine
- Strategy context/signal contracts with point-in-time validation
- Immutable multi-asset spot portfolio state and order intents
- Centralized portfolio-wide risk limits
- Explicit spot and asset-level compliance checks
- Mandatory pre-trade gate combining compliance and risk
- Causal single-asset and multi-asset backtest primitives
- Deterministic performance result and metric models
- GitHub Actions test pipeline

## Feature Engine V1

The feature engine currently computes five measurements required by the regime layer:

1. trend score
2. realized volatility
3. breadth
4. cross-sectional dispersion
5. average pairwise correlation

These are research baselines, not claimed-optimal trading indicators. Their parameters and predictive usefulness must be evaluated with the project's walk-forward and robustness protocols.

## Research principles

- Spot only; no leverage, futures, perpetuals, or short selling
- Point-in-time / no-lookahead data handling
- Finalized candles only for research features
- Explicit missing-data behavior; no silent imputation
- Deterministic outputs
- Regime classification separated from trading decisions
- `NO_TRADE` remains a valid downstream risk state
- Explicit asset compliance evidence is required before pre-trade approval

## Development

Python `>=3.13,<3.14`.

Install the package and test dependencies:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

GitHub Actions runs the same test command on Python 3.13 for pushes to `main` and pull requests.

See `docs/` for the versioned implementation contracts and research gates.
