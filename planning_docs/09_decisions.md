# Decisions

## ADR 001: Primary Transit Source
- Decision: use `511` as primary transit source for MVP
- Why:
  - covers static GTFS
  - covers historic feeds with `stop_observations`
  - covers GTFS-RT
  - avoids reconciling multiple schedule sources in MVP
- Alternatives rejected:
  - direct SFMTA GTFS as primary
  - direct SFMTA GTFS plus separate non-511 historic source

### ADR 001a: 511 Source Split
- Decision: use operator-specific SFMTA/Muni feeds for active scheduled/realtime work, and use 511 regional `RG` historic feeds for monthly historical analysis with `stop_observations`
- Why:
  - current operator-specific feeds are the cleanest path for Muni-only active schedule and realtime work
  - 511’s historic monthly analysis path is explicitly provided through regional `RG` feeds
  - `stop_observations.txt` is documented through the historic regional feed path rather than the active operator-only path
  - this split matches the actual structure of 511’s published data products
- Alternatives rejected:
  - using only operator-specific feeds for the full historical-analysis plan
  - using regional feeds for all active/current Muni work from day one

## ADR 002: MVP Transit Scope
- Decision: Muni only
- Why:
  - tighter product story
  - less irrelevant data
  - simpler route-model assumptions
- Alternatives rejected:
  - all Bay Area operators in v1

## ADR 003: Frontend Stack
- Decision: `Next.js + TypeScript`
- Why:
  - better public-facing product shell
  - natural page structure for overview, methodology, route views, and compare
  - reduces custom routing/layout/content-shell work
- Alternatives rejected:
  - `Vite + React + TypeScript` for MVP

## ADR 004: API Boundary
- Decision: separate `Python` API using `FastAPI`
- Why:
  - clean serving boundary
  - fits the pipeline language family
  - easier to test and document separately
  - better contract discipline through typed request/response models
- Alternatives rejected:
  - API routes inside the frontend app
  - `Flask` as the primary MVP API framework

## ADR 005: Data Platform
- Decision: `Python + Postgres/PostGIS + dbt`
- Why:
  - strongest transit/data-engineering fit
  - good spatial support
  - clean transformation layer
- Alternatives rejected:
  - all-TypeScript backend
  - Snowflake-centered MVP

## ADR 006: Headline Metric Language
- Decision: `Typical extra time on a full one-way trip`
- Why:
  - rider-relevant
  - does not overclaim passenger weighting
  - matches available data
- Alternatives rejected:
  - `Average rider loss` for MVP
  - `on-time %` as primary homepage metric

## ADR 007: Baseline For In-Vehicle Loss
- Decision: use scheduled trip time for MVP
- Why:
  - easiest to explain
  - available from GTFS
  - stable for early implementation
- Alternatives rejected:
  - best typical observed time as the initial published baseline

## ADR 008: Local Database Bootstrap
- Decision: use root-level `docker-compose.yml` with the official `postgis/postgis` image for local development
- Why:
  - keeps database bootstrap independent of application code
  - provides Postgres and PostGIS in one repeatable local service
  - supports early slices before Python API or pipeline code exists
- Alternatives rejected:
  - local machine Postgres install as the primary bootstrap path
  - delaying database bootstrap until the Python project exists

## ADR 009: Local Dev DB Credentials
- Decision: keep `docker-compose.yml` in git, but source local Postgres settings from a repo-root `.env` file that is gitignored
- Why:
  - removes inline local credentials from versioned config
  - keeps the local Docker bootstrap simple
  - gives a clear path to rotating throwaway dev credentials without changing committed compose files
- Alternatives rejected:
  - leaving local credentials hardcoded in `docker-compose.yml`
  - removing `docker-compose.yml` from git

## ADR 010: Initial Postgres Schema Strategy
- Decision: use Postgres schemas named `raw`, `staging`, `canonical`, `marts`, and `serving`, with GTFS static ingest starting in `raw` and the first stable scheduled interface landing in `canonical`
- Why:
  - gives `S04` and `S05` fixed namespaces and table boundaries before ingest begins
  - keeps raw-source fidelity separate from normalized scheduled entities
  - avoids overdesigning final marts or realtime structures too early
  - matches the contract-first workflow where downstream slices should not depend on raw GTFS directly
  - is closest to `dbt`-style layered modeling guidance, with `canonical` acting as the stable reusable intermediate layer
  - remains close enough to medallion architecture to explain the pattern externally without adopting `bronze/silver/gold` names literally
  - provides a clean place to preserve 511 active-feed versus historic-regional-feed provenance before reconciliation
  - supports separate batch historical refreshes and bounded-retention realtime polling/storage
- Alternatives rejected:
  - a single flat schema for all entities
  - using only table prefixes without schema separation
  - designing the full final mart and serving schema before fixture ingest is proven
  - renaming schemas to `bronze`, `silver`, and `gold`

## ADR 011: Python Bootstrap Structure
- Decision: use a root `pyproject.toml`, separate `src` packages under `api/` and `pipeline/`, and the standard-library `unittest` test runner for the early Python bootstrap
- Why:
  - keeps the API and pipeline code in separate, predictable package boundaries
  - records the `FastAPI` dependency without forcing early endpoint work
  - provides a test harness without adding more tooling than this slice needs
  - keeps later ingest and API slices free to add richer tooling once real code exists
- Alternatives rejected:
  - putting all Python code in one shared package at this stage
  - introducing `pytest` before the repo needs it
  - delaying all Python dependency metadata until a later slice

## ADR 012: Active 511 GTFS Acquisition Boundary
- Decision: keep active operator-specific `511` GTFS acquisition as a separate pipeline step that archives the downloaded zip and adjacent provenance metadata before any raw-table loading
- Why:
  - keeps network fetch concerns separate from raw-table ingest concerns
  - preserves source/operator/fetch-time provenance for later ingest and debugging
  - gives `S05` a stable upstream artifact instead of forcing canonical modeling to fetch from the network directly
  - avoids mixing active operator-specific acquisition with historic `RG` acquisition logic
- Alternatives rejected:
  - combining active `511` fetch with `raw.gtfs_*` table loading in one slice
  - storing only an unpacked directory without the original zip or provenance metadata

## ADR 013: Early Scheduled Model Materialization
- Decision: materialize the first `staging` and `canonical` scheduled GTFS models through a dedicated SQL file executed by a thin Python entrypoint before introducing a full `dbt` project
- Why:
  - keeps `S05` focused on raw-to-canonical scheduled modeling without broadening into full transformation-tool setup
  - preserves a clear raw/staging/canonical boundary while still producing DB-backed, testable tables
  - gives later slices a stable scheduled interface for observed joins and metric work
- Alternatives rejected:
  - pushing canonical scheduled logic directly into Python row transforms
  - introducing a full `dbt` project before the first scheduled canonical tables are proven

## ADR 014: Historic 511 RG Acquisition Boundary
- Decision: keep monthly historic `511` regional GTFS acquisition as a separate pipeline step that archives the downloaded zip and adjacent provenance metadata, with an explicit switch for the `-so` stop-observations variant
- Why:
  - keeps historic network fetch concerns separate from historical raw-table ingest and reconciliation work
  - preserves requested month, feed scope, and `stop_observations` intent for later staging and canonical joins
  - matches 511's documented split between plain historic `RG` feeds and the `YYYY-MM-so` variant
  - avoids mixing regional historic acquisition with the active operator-specific acquisition path
- Alternatives rejected:
  - folding historic `RG` fetch directly into `S06_historic_stop_observations_ingest`
  - treating the plain and `-so` variants as one implicit acquisition path without explicit provenance

## ADR 015: Raw Historic Stop Observations Shape
- Decision: land the first historical observation fixture in `raw.stop_observations` with source-facing join fields (`service_date`, `trip_id`, `stop_id`, `stop_sequence`, `observed_arrival_time`) plus a typed `observed_arrival_ts`
- Why:
  - keeps the raw historical observation slice narrow and usable for later scheduled/observed joins
  - preserves the source-facing timestamp text while proving timestamp parsing once during ingest
  - avoids broadening `S06` into canonical observed-event modeling
- Alternatives rejected:
  - storing only text observation timestamps and deferring all parsing
  - skipping the typed timestamp and forcing downstream slices to reparse raw text repeatedly
  - broadening `S06` into canonical observed-stop tables

### ADR 015a: Real Historic RG Observation Mapping
- Decision: load real historic `RG` archive rows into the same `raw.stop_observations` shape by mapping source `to_stop_id` to raw `stop_id`, parsing compact `service_date` values, and deriving `observed_arrival_ts` from local service-day clock times
- Why:
  - the real `stop_observations.txt` file carries more fields than the accepted raw contract, so the ingest path needs one explicit narrowing rule
  - `to_stop_id` is populated across real archive rows and matches the arrival event semantics needed by later scheduled/observed joins
  - service-day times can exceed `24:00:00`, so deriving the typed timestamp during raw load avoids repeating that edge-case parsing downstream
  - archive-backed snapshot labels should remain distinguishable from fixture labels for debugging and provenance
- Alternatives rejected:
  - expanding `raw.stop_observations` immediately to every real archive column
  - treating `from_stop_id` as the raw stop join key
  - storing real archive arrival times only as text and deferring service-day timestamp parsing

## ADR 016: First Scheduled/Observed Join Strictness
- Decision: build the first `canonical.observed_stop_events` interface as an exact join on `service_date`, `trip_id`, `stop_sequence`, and `stop_id`, and publish unmatched cases separately through explicit audit/summary views
- Why:
  - keeps `S07` narrow enough to validate one real happy path before broader historic schedule reconciliation exists
  - avoids hiding mismatch cases behind route-level or timing heuristics that would be difficult to defend this early
  - gives later waiting/runtime slices both a clean matched interface and visible unmatched counts to reason about
- Alternatives rejected:
  - fuzzy matching on nearby timestamps or partial trip keys in the first join
  - silently discarding unmatched observations without an audit surface

## ADR 017: Post-S07 Bundle Architecture
- Decision: replace the future fine-grained slices `S08` through `S35` with larger bundles `B1` through `B8`, and use lean validation as the default for the remaining roadmap
- Why:
  - the earlier roadmap described the feature path well but under-specified several infrastructure-transition steps such as real `511` acquisition boundaries and dbt introduction
  - the original slice granularity created unnecessary agent churn and slowed execution for what should remain a relatively small public-facing full-stack app
  - larger bundles keep the important subsystem boundaries while reducing repeated orchestration, review, and test overhead
  - lean validation is sufficient once the project has a stable data foundation through `S07`
- Alternatives rejected:
- continuing the old one-feature-per-slice plan after `S07`
- introducing dbt immediately before the first metrics layer is proven
- keeping dense live/integration testing on every future work unit by default

## ADR 018: First Core Metrics Scope
- Decision: compute the first published waiting loss from exact matched first-stop headways only, compute the first published in-vehicle loss from exact matched terminal-to-terminal trips only, and keep unmatched observations outside the metric numerators while surfacing them through separate coverage counts
- Why:
  - matches the conservative exact-join posture established in `S07`
  - avoids inflating waiting loss with inferred headways across missing matched trips
  - produces a defensible full-trip proxy from the current joined model, which exposes observed arrivals but not observed departures
  - gives downstream API work explicit matched-versus-unmatched diagnostics without broadening into fuzzy reconciliation
- Alternatives rejected:
- blending unmatched rows into metric math with heuristic route or timing assumptions
- computing waiting loss across non-consecutive matched trips
- delaying all route-level metrics until a richer historic reconciliation layer exists

## ADR 019: dbt Adoption Boundary
- Decision: keep Python responsible for acquisition and raw loads, but move the accepted staged, canonical, and mart transformation graph into an in-repo dbt project once `B1` metrics were proven
- Why:
  - preserves the working raw ingest entrypoints without mixing fetch/load concerns into dbt
  - gives the project a real analytics-engineering layer with source declarations, model lineage, and dbt-native tests
  - keeps the accepted metric and join semantics intact while removing the growing pile of one-off SQL materialization files from the execution path
  - allows later bundles to build on stable dbt-managed canonical and mart relations instead of bespoke Python wrappers around SQL files
- Alternatives rejected:
  - keeping the whole transformation graph as raw SQL files invoked directly from Python
  - broadening dbt into acquisition/orchestration responsibilities
  - redesigning the scheduled, observed, or mart semantics during the dbt migration itself
