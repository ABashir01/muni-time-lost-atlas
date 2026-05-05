# Tests

Reserved for repository-level automated tests.

Initial subdirectories:

- `unit/` for narrow logic tests
- `integration/` for database, API, and cross-layer tests

Slice docs should continue to define exactly which tests are required before a change is considered complete.

Current integration artifacts:

- `integration/db_smoke_test.ps1`
  - starts the local Docker Compose DB service if needed
  - waits for readiness
  - checks `PostGIS` availability
  - runs a simple connection query against `muni_lost_time_atlas`
