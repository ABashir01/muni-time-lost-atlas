# Data Sources

## Source Strategy
Use `511` as the primary transit data source for MVP.

Reason:
- it covers static GTFS
- it covers historic monthly feeds with `stop_observations`
- it covers GTFS-RT
- it avoids maintaining two competing schedule sources during MVP

Start with:
- `operator-specific SFMTA/Muni feed`

Do not start with:
- regional `RG` feed

The regional feed can be considered later if the project expands beyond Muni.

## Active Static GTFS
Primary source:
- [511 Transit Data](https://511.org/open-data/transit)

Planned usage:
- scheduled routes
- trips
- stops
- stop_times
- shapes
- service dates

Expected MVP ingest choice:
- active SFMTA/Muni operator-specific feed from 511

## Historic Monthly Feeds
Primary source:
- [511 Open Data FAQ](https://511.org/about/faq/open-data)

Planned usage:
- archived GTFS snapshots
- `stop_observations.txt` for historical observed arrivals
- route/time-window reliability metrics

These historical files are essential to the route-ranking and typical-trip calculations.

## GTFS-RT
Primary source:
- [511 Transit Data](https://511.org/open-data/transit)

Planned usage:
- live vehicle positions
- optional trip updates later if needed

GTFS-RT is a later-phase addition. Historical/static correctness comes first.

## GIS And Civic Context
Planned contextual overlays:
- [Muni Stops](https://catalog.data.gov/dataset/muni-stops)
- [Transit Only Lanes](https://catalog.data.gov/dataset/transit-only-lanes)
- [Muni Service Equity Strategy](https://www.sfmta.com/projects/muni-service-equity-strategy)

Transit-only lanes and equity layers are contextual overlays, not causal proof.

## Reference-Only SFMTA Feed
Keep direct SFMTA GTFS as a reference / validation source:
- [SFMTA GTFS transit data page](https://www.sfmta.com/vi/node/14441)

Do not treat the direct SFMTA feed as primary MVP source-of-truth unless 511 coverage is insufficient.

## Known Data Limitations
- passenger weighting is not justified from the current planned source set
- historical joins may be sensitive to route/trip/service-day quirks
- GTFS-RT should not be the core dependency for route rankings
- operator-specific 511 parsing details still need confirmation during implementation

