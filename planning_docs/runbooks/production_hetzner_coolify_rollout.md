# Production Hetzner + Coolify Rollout

## Purpose
Deploy the Muni Lost Time Atlas MVP on one Hetzner VPS, bootstrap the first rolling
3-month publication window, and operate the monthly publication cycle safely.

This runbook assumes:
- `Hetzner + Coolify`
- one VPS
- one private `Postgres/PostGIS` service
- one private `publisher` service for pipeline + dbt work
- one public `frontend` service
- one public `api` service

## Prerequisites
- a Hetzner VPS provisioned at the chosen size (`CAX31` by default)
- a domain with DNS access
- a valid `TRANSIT_511_API_KEY`
- SSH access to the VPS

## Deployment Files
Use these repo files for production:

- `docker-compose.coolify.yml`
- `frontend/Dockerfile`
- `api/Dockerfile`
- `publisher/Dockerfile`

Maintenance mode inputs:
- env override: `MAINTENANCE_MODE=true|false`
- shared flag file: `/var/run/muni-lta/maintenance.flag`

Publisher helper commands:
- `/app/publisher/bootstrap-window.sh`
- `/app/publisher/advance-window.sh`

## Phase 1: Prepare the VPS
1. Create the Hetzner VPS.
2. Install Docker.
3. Install Coolify.
4. Set up:
   - SSH key auth
   - firewall
   - automatic OS patching if desired
   - off-box backup target
   - disk-space monitoring

## Phase 2: DNS and domains
Point DNS to the VPS.

Recommended:
- `atlas.yourdomain.com` -> frontend
- `api.yourdomain.com` -> API

## Phase 3: Create the Coolify stack
In Coolify:
1. create a new application stack from this repo
2. use `docker-compose.coolify.yml`
3. define these env vars:

```text
POSTGRES_DB=muni_lost_time_atlas
POSTGRES_USER=muni
POSTGRES_PASSWORD=change_me
TRANSIT_511_API_KEY=replace_me
API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
MAINTENANCE_MODE=false
```

Notes:
- `POSTGRES_HOST` should remain `db` inside the Coolify stack
- `POSTGRES_PORT` should remain `5432`

## Phase 4: Deploy the services
Deploy in this order:

1. `db`
2. `api`
3. `frontend`
4. `publisher`

Verify:
- `db` is healthy
- `api` `/health` responds
- `frontend` loads
- `publisher` is running and can be entered for commands

## Phase 5: Verify the publisher before real data
Open a shell in the `publisher` service and verify:

```sh
python -m muni_lta_pipeline.rolling_historical_publication check-newest-available
```

This should return JSON and confirm the `publisher` can:
- read env vars
- reach the database
- reach `511`
- import the pipeline package

## Phase 6: Bootstrap the first 3 months
Run this once from the `publisher` service:

```sh
/app/publisher/bootstrap-window.sh
```

What it does:
1. creates the shared maintenance flag
2. runs `python -m muni_lta_pipeline.rolling_historical_publication bootstrap-window`
3. leaves the site in maintenance mode if bootstrap fails
4. removes maintenance mode if bootstrap succeeds

Expected bootstrap behavior:
- determine the newest completed available month from `511`
- build the trailing 3-month window ending at that month
- fetch active `SF` GTFS once
- fetch each historic monthly `RG -so` archive
- derive an `SF` archive for each month
- use Shapes API fallback when needed
- build one combined rolling-window archive
- load raw tables
- run dbt
- write publication manifests and cutover logs
- prune retained publication artifacts

After bootstrap succeeds, verify:
- homepage loads
- rankings loads
- map loads
- compare loads
- route detail loads
- `artifacts/publications/b7_rolling_historical_publication/latest.json` shows exactly 3 months

## Phase 7: Monthly publication schedule
Use a Coolify scheduled job against the `publisher` service.

### Daily check
Run daily starting on the **2nd day of each month**, around **2:00 AM Pacific**:

```sh
python -m muni_lta_pipeline.rolling_historical_publication check-newest-available
```

### Monthly advance
Run around **2:30 AM Pacific**:

```sh
/app/publisher/advance-window.sh
```

What `advance-window.sh` does:
- runs the lightweight availability check first
- compares the newest available month with the currently published latest month
- exits cleanly without maintenance mode if there is nothing to publish
- creates the maintenance flag only when a real publication advance is needed
- leaves maintenance mode on if the advance fails
- clears maintenance mode on success

## Phase 8: Backups and rollback
Minimum acceptable backup posture:
- nightly Postgres backup
- off-box retention
- at least 7-30 days

If monthly publication fails:
1. leave maintenance mode on
2. inspect:
   - `artifacts/publications/b7_rolling_historical_publication/latest.json`
   - latest cutover logs under `artifacts/publications/b7_rolling_historical_publication/cutovers/`
3. decide whether to:
   - retry publication
   - restore the previous DB backup
4. clear maintenance mode only after the site is safe to reopen

## Maintenance copy
When maintenance is enabled, the public site should say:
- scheduled maintenance is in progress
- data publication is underway
- the site should return in roughly 30 minutes
