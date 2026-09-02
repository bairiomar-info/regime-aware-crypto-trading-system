# Data Layer Specification V1

Status: **Architecture freeze / implementation contract**

Date: 2026-09-02

## 1. Purpose

This specification freezes the data-layer architecture before feature engineering, regime detection, strategy research, or portfolio code is expanded.

The system is a research-driven, long-only, spot-only quantitative trading system. The data layer must preserve historical truth, prevent survivorship and look-ahead bias, retain provenance, and make every research dataset reproducible.

## 2. Core invariants

1. Raw source artifacts are immutable.
2. Canonical data is normalized and reproducible from raw data.
3. Research datasets are versioned snapshots and are never silently overwritten.
4. Asset identity is separate from exchange symbol/instrument identity.
5. Delisted/deactivated assets remain in historical data.
6. Universe membership is point-in-time.
7. No component may consume information whose availability timestamp is later than the decision timestamp.
8. Incomplete candles are never treated as finalized research observations.
9. Missing candles are not fabricated by the canonical data layer.
10. Extreme observations are not removed merely because they are statistically unusual.
11. Conflicting lineage evidence is represented as a conflict/uncertainty, not silently resolved.
12. Research universe, strategy universe, and execution universe are distinct concepts.

## 3. Data layers

### 3.1 Raw

Exact source artifacts as obtained from an exchange/provider.

Required provenance includes, where available:
- provider
- source URL/request
- acquisition timestamp
- source artifact filename
- source checksum
- file size
- source/schema version
- retrieval status

Raw artifacts must not be edited in place.

### 3.2 Canonical

Normalized market observations with UTC timestamps, standardized field names, validated types, and explicit provenance.

Canonical records may be regenerated from raw artifacts.

### 3.3 Research dataset

A frozen dataset used by an experiment or backtest.

Must identify:
- dataset name/version
- source/canonical dataset versions
- universe version
- feature version when applicable
- code commit
- configuration hash
- creation/retrieval timestamps

## 4. Identity model

The system separates:

- `Asset`: economic asset identity.
- `Deployment`: blockchain/platform and contract/address identity where applicable.
- `ExchangeInstrument`: exchange-specific tradable market, e.g. Binance BTCUSDT.
- `Symbol`: mutable exchange label.
- External identifiers: CoinGecko ID and other provider IDs.

Ticker/symbol alone is never a permanent identity key.

## 5. Asset lifecycle

Assets can move through states such as:

- unknown
- listed
- active
- halted
- migrated
- reissued
- delisted/deactivated

Exchange-instrument lifecycle is separate from asset lifecycle.

A Binance `HALT` state must not be interpreted as delisting: Binance documents that market data can continue during HALT. `BREAK` means market data is not generated. Therefore missing candles must not automatically be classified as delisting.

## 6. Asset lineage

Create a versioned `AssetLineageEvent` concept with:

- event_id
- event_type
- effective_time
- predecessor_asset_id
- successor_asset_id
- conversion_ratio, nullable
- continuous_history, nullable/explicit
- source
- source_timestamp, nullable
- confidence
- notes

Supported event types include:

- rename
- rebrand
- migration
- chain migration
- redenomination
- reissue
- redeployment
- symbol change
- exchange listing
- exchange delisting

Pure rename/rebrand with clear economic continuity may preserve the same asset identity, but the event is still recorded.

Migration/reissue/redenomination must not be blindly spliced into a continuous return series. Continuity must be explicitly determined and recorded.

A redenomination/conversion must not create an artificial return.

## 7. Evidence hierarchy

For lineage events, preferred evidence order is:

1. Official project documentation / official blockchain evidence.
2. Official exchange documentation or announcements.
3. Direct on-chain evidence.
4. High-quality structured provider data.
5. Secondary research/reference sources.
6. Internal inference.

When strong sources conflict, record `CONFLICTED` rather than guessing. Inferred mappings must be explicitly marked as inferred.

## 8. External reference data

CoinGecko is the primary external asset-reference candidate for V1 because its coin list supports active/inactive assets and its metadata can include platform/contract information. CoinGecko IDs are reference identifiers, not the internal master identity.

Binance is the authoritative source for Binance market observations and exchange-specific execution instruments.

External reference data is stored with retrieval/provenance metadata and may be revised in later research-dataset versions.

## 9. Market observations

Canonical OHLCV records contain, at minimum:

- exchange
- instrument/symbol
- asset reference
- timeframe
- open_time
- close_time
- OHLC
- base volume
- quote volume
- trade count
- taker-buy base volume
- taker-buy quote volume
- source
- closed/finalized status

Financial numeric values must not be silently converted to binary floating-point in canonical persistence when exact decimal/string representation is required.

## 10. Candle finalization

Only closed/finalized candles are eligible for normal historical research datasets.

Current/incomplete candles may be stored as observations but must be marked non-research-eligible.

Signal timing invariant:

`closed candle -> signal -> order decision -> next executable opportunity`

A strategy may not use a candle close to execute at that same candle's close unless an execution model explicitly represents the information and latency required to do so.

## 11. Data-quality taxonomy

Data quality is divided into three concepts:

### Integrity

Hard technical validity:
- invalid timestamps
- non-positive prices
- negative volumes
- invalid OHLC relationships
- conflicting duplicates
- impossible identity/timeframe combinations

These can reject canonical records/datasets.

### Plausibility

Statistical unusualness:
- extreme returns
- unusual volume
- unusual trade counts
- stale-price indicators
- jump concentration

These are normally flags, not automatic deletion rules.

### Tradability

Whether an asset could realistically be traded:
- liquidity
- exchange status
- market availability
- execution constraints

These belong to universe/execution eligibility, not canonical integrity.

## 12. Missing intervals

A missing interval is not automatically an error.

The quality system must distinguish at least:

- `NO_TRADES`
- `DATA_GAP`
- `SOURCE_FAILURE`
- `HALT`
- `BREAK`
- `UNKNOWN_GAP`

Canonical data must not fabricate candles.

If evidence cannot distinguish a no-trade interval from a source failure, retain the uncertainty and flag the interval.

The current acquisition service rule that rejects every interval gap must therefore be changed before production research use.

## 13. Duplicates

Duplicate candles with identical identity and identical values may be collapsed with a recorded duplicate count.

Conflicting duplicates for the same identity/time are hard quality failures until resolved.

## 14. Historical acquisition

For large Binance Spot historical backfills:

`official Binance Public Data archive -> raw artifact -> checksum verification -> canonical normalization`

For recent/incremental acquisition:

`Binance Spot API -> raw response/provenance -> canonical normalization`

Archive and API observations must pass through the same canonical contract.

Archive files and checksums must be retained as provenance. Archived files may later be corrected by Binance; therefore source retrieval date and checksum are part of dataset identity.

## 15. Acquisition resumability

Acquisition checkpoints must become operational, not merely model definitions.

A resumable acquisition must record:
- request identity
- chunk identity
- last successful boundary
- status
- attempts/errors
- source artifact(s)
- validation outcome

A restart must continue from the last durable successful boundary without silently duplicating or losing observations.

## 16. Historical universe

Universe construction is point-in-time.

At each decision timestamp:

`historically known assets -> lifecycle -> instrument availability -> data quality -> feature readiness -> liquidity -> classification -> strategy-specific universe`

Current exchange listings must never be projected backward to represent historical membership.

## 17. Universe layers

### Raw market universe

Everything historically identifiable.

### Research universe

Point-in-time assets meeting general research requirements.

### Strategy universe

Research universe plus strategy-specific requirements.

### Execution universe

Strategy candidates that can actually be traded under position-size, liquidity, exchange, and execution constraints.

## 18. Universe membership record

A versioned point-in-time membership record should contain:

- timestamp
- asset_id
- exchange_instrument_id where relevant
- eligible
- exclusion reason(s)
- universe version
- relevant metric snapshots

Possible reasons:

- `NOT_YET_LISTED`
- `DELISTED`
- `HALTED`
- `INSUFFICIENT_HISTORY`
- `INSUFFICIENT_LIQUIDITY`
- `DATA_QUALITY_FAILURE`
- `UNSUPPORTED_ASSET_CLASS`
- `UNKNOWN_IDENTITY`
- `LINEAGE_CONFLICT`
- `INSUFFICIENT_UNIVERSE_BREADTH`

## 19. Feature readiness

Asset age and strategy readiness are separate.

Readiness states:

- `NOT_READY`
- `INSUFFICIENT_HISTORY`
- `READY_FOR_FEATURES`
- `READY_FOR_STRATEGY`

Warm-up requirements are feature/strategy-specific. There is no universal fixed asset-age threshold in V1.

No backfilling is used to manufacture missing history.

## 20. Liquidity

V1 market-universe liquidity is based on rolling quote/dollar volume rather than base-asset volume.

The conceptual liquidity screen contains:

- typical rolling quote volume
- valid-observation coverage
- liquidity consistency
- recent deterioration

Exact window, statistic, and threshold remain research parameters.

Median rolling volume is the preferred initial candidate because it is less dominated by isolated spikes, but mean/median/percentile alternatives must be tested before freezing a numerical threshold.

Execution liquidity is separate and may later incorporate:

- spread
- order-book depth
- expected participation
- price impact
- execution horizon
- expected position size

## 21. Market capitalization

Historical circulating market capitalization is point-in-time information.

Market cap is not a universal hard filter in V1.

It may be used as:
- a feature
- a ranking input
- a portfolio/risk input
- a market-state input
- a strategy-specific eligibility variable when justified by research

FDV is stored separately and must not replace circulating market cap.

## 22. Asset classification

Classification is multidimensional and may include:

- ordinary standalone asset
- stablecoin
- wrapped/pegged asset
- synthetic/leveraged product
- sector/function category
- underlying exposure

Stablecoins are not ranked as ordinary momentum candidates in the primary opportunity universe. They remain available for defensive/risk/depeg research.

Classification rules must be point-in-time where the classification itself can change.

## 23. Minimum universe breadth

If a strategy requires a cross-section and too few assets satisfy its requirements, the strategy becomes inactive rather than silently changing into a different strategy.

The exact minimum breadth is an experiment.

## 24. Provenance

Existing provenance models must be extended over time to capture:

- source provider
- source type
- source URL/request
- acquired_at
- source checksum where applicable
- artifact size where applicable
- normalization version
- validation version
- schema version
- dataset version
- universe version
- code commit/config hash for research datasets

## 25. Dataset versioning

A research dataset must be reproducible from:

`raw source versions + canonical schema/version + lineage version + universe version + feature version + code commit + configuration`

When historical provider data or lineage interpretation changes, create a new dataset version instead of mutating the old research snapshot.

## 26. Temporal integrity

Every derived observation must be computed only from information available at or before its decision timestamp.

Forbidden examples:

- future delisting information used to define a historical universe
- current market cap applied backward
- future liquidity used for historical ranking
- global mean/std normalization
- same-candle close execution
- incomplete higher-timeframe candle used in a finalized signal
- full-history HMM smoothing used for historical decisions
- forward-filling missing market observations with future information

## 27. Current repository gaps to address

The current repository already has useful acquisition, normalization, validation, Parquet storage, manifests, and checkpoint models. The existing `AcquisitionCheckpoint` is defined but resumability is not yet fully operational. The acquisition service currently treats any interval gap as fatal, which conflicts with the V1 missing-interval taxonomy. Existing storage provenance does not yet contain all raw-artifact/checksum/research-snapshot fields required by this specification.

These are implementation tasks, not reasons to redesign the architecture.

## 28. Implementation order after this specification

1. Add/adjust identity and lifecycle models.
2. Add lineage-event models and evidence/confidence fields.
3. Add historical external-reference ingestion boundary.
4. Extend provenance and dataset identity.
5. Implement raw artifact/checksum metadata.
6. Implement resumable acquisition.
7. Replace fatal-gap logic with typed quality classification.
8. Add point-in-time universe membership model/service.
9. Add feature-readiness and liquidity interfaces without freezing experimental numerical thresholds.
10. Build a small historical fixture dataset and validate all invariants.
11. Only then begin feature-engineering research.

## 29. Explicit non-goals for V1

Do not add yet:

- machine-learning asset identity resolution
- automatic AI lineage merging
- sentiment data
- social-media signals
- on-chain signals
- order-book microstructure as a primary universe filter
- complex data lake infrastructure
- MLflow or experiment-management platforms
- automatic candle repair/fabrication
- a universal liquidity threshold
- a universal market-cap threshold

## 30. Acceptance criteria

The data layer is considered ready for feature/regime research only when:

- historical identity is separated from mutable exchange symbols;
- delisted assets can remain historically represented;
- lineage is explicit and versioned;
- raw artifacts are immutable and checksummed where possible;
- acquisition can resume safely;
- missing intervals are classified rather than universally rejected;
- only finalized observations enter normal research datasets;
- universe membership is point-in-time;
- feature readiness is explicit;
- liquidity uses point-in-time quote-volume information;
- market cap is point-in-time;
- provenance can reproduce a research dataset;
- temporal-integrity tests prevent future information leakage;
- the same canonical contract works for archive and API acquisition.
