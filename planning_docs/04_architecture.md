# Architecture

## System Shape
The MVP is a simple four-part system:
- data platform
- Postgres/PostGIS database
- thin FastAPI service
- Next.js frontend

The intended runtime flow is:
- `511 -> Python fetch/load -> Postgres raw tables -> SQL/dbt transforms -> marts -> FastAPI -> Next.js`

## Data Platform
Use:
- `Python` for acquisition, archive handling, extraction, and raw loads
- SQL-first transformations until the first metrics layer is stable
- `dbt` after the first metrics bundle is proven

Data-platform responsibilities:
- fetch active operator GTFS from `511`
- fetch historic `RG` archives from `511`
- fetch GTFS-RT later
- load raw GTFS and raw stop observations into Postgres
- enrich recent historic cutovers with build-time Shapes API geometry fallback
  when monthly archives omit `shapes.txt`
- materialize scheduled canonical models
- materialize observed canonical models
- materialize route and segment marts

Important boundary:
- Python owns acquisition and raw landing
- dbt owns staged/canonical/mart modeling after raw data is landed
- dbt does not replace Python fetch/load code

## Database
Use:
- `Postgres + PostGIS`

Database responsibilities:
- raw source-of-truth relational storage
- canonical and mart storage
- spatial storage for route/stop/segment geometry
- thin serving queries for the API

Layering model:
- `raw`
- `staging`
- `canonical`
- `marts`
- `serving` only if a later API bundle needs extra read-optimized views

Current implementation note:
- Python still owns raw acquisition and raw-table loads
- after `B2`, the staged/canonical/mart graph lives in the in-repo `dbt/` project
- after `B3`, the same dbt project also materializes the first `serving` spatial layers for route, stop, segment, and overlay map reads

## API
Use:
- separate `Python` API using `FastAPI`

API responsibilities:
- expose stable, documented response shapes
- read from canonical or mart tables only
- avoid embedding metric logic in request handlers

Implementation preference:
- `Pydantic` request/response models
- targeted SQL access through `SQLAlchemy Core` or `psycopg`
- no heavy ORM-first design

Historical/static endpoints:
- `GET /health`
- `GET /rankings`
- `GET /routes/{route_id}/summary`
- `GET /routes/{route_id}/segments`
- `GET /routes/compare`
- `GET /map/routes`

Deferred realtime endpoint:
- `GET /live/vehicles`

## Frontend
Use:
- `Next.js + TypeScript`

Current implementation note:
- the first public frontend used a controlled SVG/schematic map surface to stabilize the homepage composition and static review workflow
- a later explicit bundle should replace that schematic surface with a real map engine
- selected map-engine direction for the real cutover: `MapLibre GL JS`

Frontend responsibilities:
- homepage rankings and explainer hierarchy
- route detail
- compare view
- map view
- methodology page
- loading, empty, and error states

Important boundary:
- frontend does not compute transit metrics directly
- frontend should consume fixture payloads first, then live API payloads
- the product hierarchy remains:
  - rankings first
  - map second
  - explanatory context third

Map-engine guidance:
- the accepted homepage composition should survive the map-library transition
- the real map should support:
  - route geometry
  - segment layers
  - stop wait hotspots later
  - transit-lane overlay context
  - GTFS-RT vehicle overlays later
- the map engine should not force a generic full-screen mapping app layout if that breaks the editorial product structure
- this choice should demonstrate practical web-GIS fluency:
  - layered route and segment styling
  - overlay handling
  - viewport/bounds management
  - clean GeoJSON-to-map rendering

## dbt Role
dbt is a later, explicit bundle rather than an implicit promise.

dbt will own:
- source declarations
- `staging` models
- `canonical` models
- `marts`
- `serving` read models when thin API-oriented spatial layers are justified
- dbt-native model tests

dbt will not own:
- `511` acquisition
- zip archive downloads
- raw file extraction
- API serving
- frontend logic

The correct introduction point is:
- after the first metric graph is proven in SQL-first form
- before the API and frontend depend on a larger, still-moving transformation graph

Current implementation note:
- that introduction point is now complete
- use the Python loaders to land `raw` data first, then run dbt for `staging`, `canonical`, and `marts`

## Deployment Shape
Expected deployables:
- one reverse proxy
- one frontend app
- one Python API service
- one Postgres/PostGIS database

Preferred MVP runtime:
- one VPS
- one Docker Compose stack
- `Postgres/PostGIS`
- `FastAPI`
- `Next.js`
- `Caddy` or `Nginx`

Operational guidance:
- keep historical analytics batch-driven
- keep the live serving database on a rolling historical window rather than a full historical archive
- publish on a monthly cadence rather than pretending the metrics are realtime
- older monthly archives should be retained outside the primary live serving DB

## Real Dataset Cutover
Current implementation note:
- the system has real historic/archive acquisition and raw-load plumbing
- but the app-facing development path initially used a constrained published dataset to keep tests and UI wiring deterministic

The explicit cutover bundle should:
- choose one or more real historical months
- run the full staged/canonical/mart graph against real scheduled and observed data
- populate the historical/static API from that larger real dataset
- replace the visible two-route development cut with broader route coverage

Important boundary:
- the real dataset cutover should happen before or alongside the real map-engine bundle
- it should happen before rolling historical publication is treated as the next major user-facing priority
- if recent monthly archives lack `shapes.txt`, recent metric builds may use
  monthly archive schedules and observations plus current Shapes API geometry
  fallback during the build
