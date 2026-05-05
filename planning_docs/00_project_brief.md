# Muni Lost Time Atlas Project Brief

## Project Thesis
`Muni Lost Time Atlas` is a public-facing transit reliability product that answers one clear civic question:

**Where do Muni riders lose the most time, and when?**

The project should translate transit operations into rider consequences. It should not feel like a generic dashboard or a repackaging of existing agency KPIs. The product should foreground extra time lost through irregular waits and slow travel, then explain where and when that loss happens.

## Audience
Primary audiences:
- public-facing readers interested in San Francisco transit
- editors or reviewers evaluating a submission for the San Francisco Standard open call
- transit agencies or transit-adjacent employers assessing transit fluency
- hiring managers assessing GIS, data engineering, analytics engineering, and product execution

Secondary audiences:
- technically curious users who want methodology and sources
- transit advocates who want route-level and corridor-level evidence

## Goals
- show clear `GIS` signal through a strong route map, geometry handling, and spatial overlays
- show clear `transit` signal through route/headway/runtime understanding and reliable terminology
- show clear `data / analytics engineering` signal through ingest, modeling, tested metrics, and documented methodology
- show clear `product` signal through a coherent, public-facing experience rather than a backend-only exercise

## Why This Fits The Standard
This project is a good fit for the Standard because:
- it is distinctly San Francisco
- it uses public transit data in a way that surfaces a buried civic question
- it turns public data into a sharper public-interest interactive rather than a generic dashboard
- it can be submitted as a working prototype plus pitch, which is realistic for the target build window

## MVP Boundaries
The MVP should be:
- `Muni only`
- `route rankings + map + route detail + compare + methodology`
- grounded in official public data
- historically correct before it becomes realtime-rich

The MVP should not try to:
- cover all Bay Area agencies
- make causal claims about transit-only lanes
- claim passenger-weighted rider burden without supporting data
- solve every corridor segmentation problem upfront

## Default Technical Direction
- `511` is the primary transit data source
- use `operator-specific SFMTA/Muni feeds` from 511, not the regional `RG` feed, for MVP
- `Next.js + TypeScript` frontend
- separate `Python` API using `FastAPI`
- `Python + Postgres/PostGIS + dbt` data platform
- build in `very small slices`

## MVP Success Criteria
The MVP is successful when:
- a user can see which Muni routes lose the most time in a selected time window
- a user can understand whether the problem is waiting, travel time, or both
- a user can inspect where on the route the loss is worst
- the metric definitions are explicit and defensible
- the data/model/API/UI path is clean enough to demonstrate engineering quality

## Relationship To Other Docs
- product behavior lives in [01_product_experience.md](./01_product_experience.md)
- metric language and math live in [02_methodology.md](./02_methodology.md)
- source-of-truth data decisions live in [03_data_sources.md](./03_data_sources.md)
- implementation order lives in [07_build_sequence.md](./07_build_sequence.md)
