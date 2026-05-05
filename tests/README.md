# Tests

Reserved for repository-level automated tests.

Initial subdirectories:

- `unit/` for narrow logic tests
- `integration/` for database, API, and cross-layer tests

Slice docs should continue to define exactly which tests are required before a change is considered complete.

Current integration artifacts:

- `integration/db_smoke_test.ps1`
  - expects a local `.env` file at the repo root
  - starts the local Docker Compose DB service if needed
  - confirms the `db` service is running
  - retries one simple `psql` query until it succeeds
  - proves the query can read `current_database()`, `current_user`, and `PostGIS_Version()`
