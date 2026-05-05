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
  - regional RG feed for MVP

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
