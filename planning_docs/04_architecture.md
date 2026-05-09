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
- one frontend app
- one Python API service
- one Postgres/PostGIS database

Operational guidance:
- keep historical analytics batch-driven
- keep realtime ingestion separate from historical marts
- do not recompute the full historical metrics layer on every realtime poll
