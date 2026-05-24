# Deployment Strategy

## Decision
Deploy the MVP as a single always-on application on one VPS using Docker Compose.

Use:
- one VPS
- one `docker compose` stack
- `Postgres/PostGIS`
- `FastAPI`
- `Next.js`
- `Caddy` or `Nginx` as the reverse proxy and TLS terminator

Do not use:
- `BigQuery` as the serving store
- `DuckDB` as the primary production database
- separate managed frontend/backend/database products unless later traffic or ops needs justify the extra cost

## Why This Is The Chosen Shape
This project is:
- mostly reading precomputed marts
- spatial but still modest in scale
- not highly concurrent at MVP scale
- operationally simple enough to keep on one box

A single VPS replaces:
- managed database cost
- separate frontend hosting cost
- separate API hosting cost

The tradeoff is:
- we own backups
- we own deploys
- we own uptime/recovery

That is acceptable for the MVP.

## Data Retention Decision
Use a **rolling 6-month live database window**.

Keep:
- the last 6 months in the serving `Postgres/PostGIS` database
- older monthly source and derived archives in retained artifact storage outside the live serving window

Reason:
- 6 months preserves real date-range utility
- 6 months stays operationally reasonable in a single Postgres instance
- the full historical archive is better retained as cold artifacts than as the live serving database

## Measured Baseline
Using the accepted `2026-04` cutover:
- live Postgres database footprint: about `13.36 GiB` for one month
- source regional archive zip: about `577.7 MB`
- derived SF-only archive zip: about `207.2 MB`

Estimated live DB sizes if scaled roughly linearly:
- 1 month: about `13.36 GiB`
- 3 months: about `40.07 GiB`
- 6 months: about `80.15 GiB`

Estimated archive-storage totals if retained:
- 1 month source + derived zips: about `0.78 GB`
- 3 months: about `2.35 GB`
- 6 months: about `4.71 GB`

## Why 6 Months Instead Of 3 Or 1
### 1 month
Pros:
- cheapest
- simplest

Cons:
- weak historical comparison value
- date range becomes barely meaningful
- product starts to feel like a recent snapshot tool rather than a historical atlas

### 3 months
Pros:
- much cheaper than 6 months
- still allows limited date-range exploration

Cons:
- weaker seasonal and recurring-pattern usefulness
- easier to fall into partial-story conclusions

### 6 months
Pros:
- enough history for real date-range use
- better public/product credibility
- still feasible on one VPS with Postgres/PostGIS

Cons:
- larger live DB
- more expensive than 1 or 3 months

Decision:
- choose **6 months** as the default live retention window
- keep the architecture compatible with reducing to 3 months later if deployment cost becomes a problem

## Recommended Runtime Topology
### Services
- `db`
  - `postgis/postgis`
  - persistent volume
- `api`
  - `FastAPI`
  - internal-only container port
- `frontend`
  - `Next.js`
  - internal-only container port
- `proxy`
  - `Caddy` or `Nginx`
  - public `80/443`

### Network shape
- only the reverse proxy is publicly exposed
- `Postgres` should not be public
- API and frontend should sit behind the reverse proxy on the Docker network

### Persistent state
- Postgres data volume
- optional retained cutover/archive volume
- logs can remain local at MVP scale, but should be rotated

## Operational Responsibilities On A VPS
The VPS approach is the cheapest, but it requires basic ops ownership.

Required:
- Docker and Docker Compose install
- OS patching
- firewall configuration
- DNS setup
- TLS setup
- deployment commands or deployment script
- Postgres volume persistence
- regular backups
- restore procedure
- disk-space monitoring
- container health monitoring

Minimum acceptable backup posture:
- nightly Postgres backup
- off-box backup target
- at least 7-30 days retention

## Why Not BigQuery
BigQuery is not the right serving database for this MVP.

Reasons:
- the product serves precomputed marts, not warehouse-first exploratory SQL
- a web app would still need an always-on API/service layer
- query-cost variability is not attractive for a modest public app
- Postgres/PostGIS is a much better fit for map serving and app-facing row retrieval

## Why Not DuckDB As The Primary Production Store
DuckDB is useful as an analytics-engineering signal and optional sidecar analysis tool, but not as the main app-serving database here.

Reasons:
- weaker fit for concurrent always-on web serving
- weaker fit than PostGIS for the map-serving/storage role
- less conventional for the full-stack public app shape we actually have

DuckDB can still be added later for:
- reproducible offline analysis cuts
- local profiling
- portfolio-side analytical artifacts

## Deployment Recommendation
Preferred MVP deploy target:
- one VPS
- Docker Compose
- `Postgres/PostGIS`
- `FastAPI`
- `Next.js`
- `Caddy`
- rolling 6-month live DB window
- older archives retained separately

This is the best balance of:
- always-on availability
- lowest practical cost
- honest spatial/data-engineering architecture
- low enough complexity to ship
