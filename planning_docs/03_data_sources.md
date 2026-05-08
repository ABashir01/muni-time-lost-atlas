# Data Sources

## Source Strategy
Use `511` as the primary transit data source for MVP.

Reason:
- it covers static GTFS
- it covers historic monthly feeds with `stop_observations`
- it covers GTFS-RT
- it avoids maintaining two competing schedule sources during MVP

The project should use two different 511 source paths:
- `operator-specific SFMTA/Muni feeds` for current scheduled and realtime operator-specific work
- `regional RG historic feeds` for monthly historical analysis, including `stop_observations`

This split is important because the historic analysis features depend on 511’s historic regional feed structure rather than only the active operator-specific feed.

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

This is the right source for:
- current scheduled GTFS structure
- current Muni-only scheduled baseline work
- later comparison against historic modeled results

## Historic Monthly Feeds
Primary source:
- [511 Open Data FAQ](https://511.org/about/faq/open-data)

Planned usage:
- archived GTFS snapshots
- `stop_observations.txt` for historical observed arrivals
- route/time-window reliability metrics

These historical files are essential to the route-ranking and typical-trip calculations.

Expected MVP ingest choice:
- `operator_id=RG` historic regional feeds from 511

Important source notes from 511:
- historic regional feeds are downloaded via the `RG` feed path
- `stop_observations.txt` is available via the historic regional feed with the `-so` suffix
- historic feeds differ structurally from active feeds:
  - `calendar.txt` is removed and rewritten into `calendar_dates.txt`
  - `trips.txt` records are hashed and compared
  - global IDs are namespaced

This means historical analysis should be modeled from the historic regional feed and then filtered to Muni/SFMTA in staging or canonical layers.

## GTFS-RT
Primary source:
- [511 Transit Data](https://511.org/open-data/transit)

Planned usage:
- live vehicle positions
- optional trip updates later if needed

Expected MVP ingest choice:
- active SFMTA/Muni operator-specific GTFS-RT feeds from 511

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
- historical joins may be sensitive to route/trip/service-day quirks and to active-vs-historic feed structural differences
- GTFS-RT should not be the core dependency for route rankings
- historic regional feed reconciliation must account for namespaced IDs, trip hashing, and `calendar_dates`-only service history
