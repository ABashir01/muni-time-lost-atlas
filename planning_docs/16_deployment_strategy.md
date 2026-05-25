# Deployment Strategy

## Decision
Deploy the MVP as a single always-on application on one VPS, with **Hetzner + Coolify** as the default operating assumption.

Use:
- one Hetzner VPS
- Coolify as the default deployment/control layer
- `Postgres/PostGIS`
- `FastAPI`
- `Next.js`
- `Caddy` or `Nginx` as the reverse proxy and TLS terminator

Fallback if Coolify becomes unnecessary:
- plain `docker compose` on the same Hetzner VPS

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

A single Hetzner VPS replaces:
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

For the `B7` publication implementation specifically:
- the live DB is rolling
- and the publication-owned on-disk artifacts are pruned after each successful publish so they do not grow without bound on the VPS

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

## Hosting Assumption
Preferred MVP host:
- Hetzner

Preferred deployment control layer:
- self-hosted Coolify on the same VPS

Reason:
- much cheaper than typical managed app + managed DB combinations
- easier day-to-day deployment management than raw manual Docker alone
- still fully compatible with a one-box Postgres/PostGIS + API + frontend architecture

If a clearly cheaper and easier VPS/VM option appears later, this can be revisited, but the current default assumption should be:
- `Hetzner + Coolify`

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
- Coolify should manage the deployed services, env vars, and restarts rather than requiring ad hoc manual container management

### Persistent state
- Postgres data volume
- optional retained cutover/archive volume
- logs can remain local at MVP scale, but should be rotated

## Publication Cadence
The production app should update on a **monthly** historical-publication cadence.

Use:
- a daily cron or scheduled job on the Hetzner VPS
- a lightweight availability check for the newest completed historic month
- the full rolling-window cutover only when a new month is actually available

Current verified source behavior:
- on `2026-05-24`, `511` returned `404` for `historic=2026-05-so`
- on `2026-05-24`, `511` returned `200` for `historic=2026-04-so`

Operational interpretation:
- `511` is exposing the **last completed month**
- the source should be treated as retrospective monthly publication, not as a continuously updated current-month archive

Recommended first cron policy:
- run the check daily starting on the **2nd** of each month
- run the availability check during a low-traffic overnight window, such as around `2:00 AM` Pacific
- if the new completed month becomes available, run the publication maintenance window immediately after, such as around `2:30 AM` Pacific
- publish once the new completed month becomes available
- do nothing when the month is still unavailable or already published

Operational runbook:
- `planning_docs/runbooks/B7_rolling_historical_publication.md`

## First Production Population
The first production deployment should **bootstrap the full live rolling window immediately**.

Do not:
- deploy with only one month and wait for the window to fill naturally

Do:
- identify the newest completed month currently available from `511`
- select that month plus the prior `5` completed months
- build and publish the full 6-month live window before treating the deployment as complete

Example:
- if the newest available month is `2026-04`
- the first production live window should be:
  - `2025-11`
  - `2025-12`
  - `2026-01`
  - `2026-02`
  - `2026-03`
  - `2026-04`

### First-deploy workflow
1. provision the VPS and deploy the application stack
2. verify the app and database services are healthy
3. determine the newest completed month available from `511`
4. compute the 6-month bootstrap window ending at that month
5. run the monthly cutover/build flow for each month in that bootstrap window
6. publish the resulting 6-month retained dataset into the live serving DB
7. verify homepage, rankings, compare, route detail, and map against the populated live window
8. enable the normal monthly availability-check cron only after the initial bootstrap succeeds

### Operational rule
The bootstrap path and the steady-state monthly publication path are different:
- bootstrap fills the initial 6-month live window
- steady-state publication advances that window by one completed month at a time

## Operational Responsibilities On A VPS
The VPS approach is the cheapest, but it requires basic ops ownership.

Required:
- Hetzner VPS provisioning
- Coolify install and upkeep
- Docker and Docker Compose install beneath Coolify
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
- one Hetzner VPS
- Coolify
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
