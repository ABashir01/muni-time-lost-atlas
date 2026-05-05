param(
    [int]$MaxAttempts = 24,
    [int]$SleepSeconds = 5
)

$ErrorActionPreference = "Stop"

function Invoke-Compose {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    & docker compose @Args
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Starting local Postgres/PostGIS service..."
Invoke-Compose up -d db

$ready = $false
for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    try {
        & docker compose exec -T db pg_isready -U muni -d muni_lost_time_atlas | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
    }
    catch {
    }

    Start-Sleep -Seconds $SleepSeconds
}

if (-not $ready) {
    throw "Database did not become ready after $MaxAttempts attempts."
}

Write-Host "Checking PostGIS extension availability..."
$postgisVersion = & docker compose exec -T db psql -U muni -d muni_lost_time_atlas -t -A -c "SELECT PostGIS_Version();"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to query PostGIS version."
}

if ([string]::IsNullOrWhiteSpace($postgisVersion)) {
    throw "PostGIS version query returned an empty result."
}

Write-Host "Checking project-level connection query..."
$connectionCheck = & docker compose exec -T db psql -U muni -d muni_lost_time_atlas -t -A -c "SELECT current_database() || '|' || current_user;"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to run connection smoke test query."
}

Write-Host "PostGIS version: $postgisVersion"
Write-Host "Connection check: $connectionCheck"
Write-Host "DB smoke test passed."
