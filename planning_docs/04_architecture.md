# Architecture

## System Shape
The MVP should be composed of four major parts:
- frontend application
- thin serving API
- data platform
- planning/documentation layer

## Frontend
Use:
- `Next.js + TypeScript`

Reason:
- public-facing homepage and methodology content fit naturally
- route pages and compare/map pages fit a page-oriented shell
- the product needs more than a pure SPA map surface

Frontend responsibilities:
- route rankings presentation
- map rendering
- route detail views
- compare views
- methodology presentation
- loading, error, and empty states

## API
Use:
- separate `Python` API using `FastAPI`

Reason:
- clear boundary between serving and UI
- cleaner tests and contracts
- keeps transit/data logic closer to the pipeline language family
- typed request and response models fit the documented contract-first workflow

API responsibilities:
- rankings endpoint
- route summary endpoint
- map geometry and metric endpoints
- compare endpoint
- live vehicle endpoint later

Implementation preference:
- use `Pydantic` models for request and response validation
- prefer `SQLAlchemy Core` or `psycopg` for targeted DB access over a heavy ORM-first design

## Database
Use:
- `Postgres + PostGIS`

Responsibilities:
- source-of-truth relational store
- spatial storage and spatial joins
- serving precomputed marts
- route and segment geometry support

## Data Platform
Use:
- `Python` for ingest and parsing
- `dbt` for transformations and marts

Responsibilities:
- GTFS static ingest
- historic stop observation ingest
- GTFS-RT ingest later
- canonical scheduled models
- canonical observed models
- route/segment aggregate marts

## System Boundaries
- frontend does not compute transit metrics directly
- API serves stable response shapes from precomputed data
- data platform owns ingest, normalization, and metric computation
- methodology and planning docs describe the contract and rationale

## Deployment Shape
Expected deployables:
- one frontend app
- one Python API service
- one Postgres/PostGIS database

Scheduling/orchestration can start simple and remain implementation-detail scope until the pipeline is active.
