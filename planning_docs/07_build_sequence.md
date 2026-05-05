# Build Sequence

## Build Strategy
Build from the inside out:
1. prove scheduled and historical data ingest
2. prove the metric math
3. freeze a small API contract
4. build the UI against fixtures
5. wire the UI to live endpoints
6. add GTFS-RT only after the static/historical MVP works

## Ordered Slice List
### Foundation
- `S01_repo_structure`
- `S02_database_bootstrap`
- `S03_python_project_bootstrap`
- `S03a_schema_strategy`

### Static / Historical Data
- `S04_gtfs_static_fixture_ingest`
- `S05_canonical_scheduled_models`
- `S06_historic_stop_observations_ingest`
- `S07_scheduled_observed_join`

### Metric Proof
- `S08_waiting_time_math`
- `S09_in_vehicle_loss_math`
- `S10_route_level_metric`
- `S11_metrics_mart_prototype`

### GIS Layer
- `S12_geometry_ingest`
- `S13_transit_lane_overlay`
- `S14_segment_loss_prototype`

### API Layer
- `S15_api_skeleton`
- `S16_rankings_endpoint`
- `S17_route_summary_endpoint`
- `S18_map_endpoints`
- `S19_compare_endpoint`

### Frontend Shell
- `S20_next_app_skeleton`
- `S21_design_system_primitives`
- `S22_homepage_with_fixtures`
- `S23_map_view_with_fixtures`
- `S24_route_detail_with_fixtures`
- `S25_compare_view_with_fixtures`

### Frontend Integration
- `S26_rankings_integration`
- `S27_route_detail_integration`
- `S28_map_integration`
- `S29_compare_integration`

### Realtime
- `S30_gtfs_rt_ingest`
- `S31_live_vehicle_endpoint`
- `S32_live_map_overlay`

### Hardening
- `S33_methodology_page_finalization`
- `S34_qa_edge_cases`
- `S35_mvp_polish`

## Phase Gates
Before moving from one phase to the next, these conditions must hold:

### Before API work
- static/historical ingest works on fixtures
- the metric math is tested
- the route-level metric definition is locked

### Before frontend live integration
- API response shapes are documented
- fixture payloads exist
- endpoint integration tests pass

### Before realtime work
- historical/static MVP is trustworthy
- frontend map works without live vehicles
