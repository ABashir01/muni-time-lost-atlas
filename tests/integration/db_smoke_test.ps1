param(
    [int]$MaxAttempts = 12,
    [int]$SleepSeconds = 2
)

$ErrorActionPreference = "Stop"
$envFile = Join-Path $PSScriptRoot "..\..\.env"

if (-not (Test-Path $envFile)) {
    throw "Missing .env at repo root. Copy .env.example to .env and set local DB values before running the smoke test."
}

function Get-EnvFileValues {
    param(
        [string]$Path
    )

    $values = @{}
    foreach ($line in Get-Content $Path) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $trimmed = $line.Trim()
        if ($trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed -split "=", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $values[$parts[0].Trim()] = $parts[1].Trim()
    }

    return $values
}

$envValues = Get-EnvFileValues -Path $envFile
$requiredKeys = @("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
foreach ($key in $requiredKeys) {
    if (-not $envValues.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($envValues[$key])) {
        throw "Missing required key '$key' in .env."
    }
}

$postgresDb = $envValues["POSTGRES_DB"]
$postgresUser = $envValues["POSTGRES_USER"]
$postgresPassword = $envValues["POSTGRES_PASSWORD"]
$query = "SELECT current_database() || '|' || current_user || '|' || PostGIS_Version();"

Write-Host "Starting local Postgres/PostGIS service..."
& docker compose up -d db
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up -d db failed with exit code $LASTEXITCODE"
}

$runningServices = (& docker compose ps --services --status running).Trim()
if ($LASTEXITCODE -ne 0 -or -not ($runningServices -split "\r?\n" | Where-Object { $_ -eq "db" })) {
    throw "The db service is not running."
}

$result = $null
for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Write-Host "Running DB smoke query (attempt $attempt of $MaxAttempts)..."
    $result = & docker compose exec -T -e PGPASSWORD=$postgresPassword db psql -h 127.0.0.1 -U $postgresUser -d $postgresDb -t -A -c $query 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($result)) {
        break
    }

    $result = $null
    Start-Sleep -Seconds $SleepSeconds
}

if ([string]::IsNullOrWhiteSpace($result)) {
    throw "The DB smoke query did not succeed after $MaxAttempts attempts."
}

Write-Host "Smoke query result: $($result.Trim())"
Write-Host "DB smoke test passed."
