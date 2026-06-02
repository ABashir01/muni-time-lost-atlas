param(
    [switch]$SkipDockerBuild,
    [switch]$RunHostPythonSmoke,
    [switch]$SkipPythonSync
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$composeFile = Join-Path $repoRoot "docker-compose.coolify.yml"
$envFile = Join-Path $repoRoot ".env"

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = "python"
}

Write-Host "Phase 1/4: starting the local Docker Compose DB used by the publisher smoke..."
& docker compose --env-file $envFile -f $composeFile up -d db
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up -d db failed with exit code $LASTEXITCODE"
}

$dbReady = $false
for ($attempt = 1; $attempt -le 12; $attempt++) {
    Write-Host "Checking publisher-smoke DB readiness (attempt $attempt of 12)..."
    & docker compose --env-file $envFile -f $composeFile exec -T db sh -lc 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    if ($LASTEXITCODE -eq 0) {
        $dbReady = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $dbReady) {
    throw "The publisher-smoke DB did not become ready."
}

if (-not $SkipDockerBuild) {
    Write-Host "Phase 2/4: rebuilding the publisher image locally..."
    & docker compose --env-file $envFile -f $composeFile build publisher
    if ($LASTEXITCODE -ne 0) {
        throw "Publisher Docker build failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Host "Phase 2/4: skipping publisher Docker build."
}

Write-Host "Phase 3/4: running the publisher smoke inside the local publisher container..."
& docker compose --env-file $envFile -f $composeFile run --rm publisher python -m muni_lta_pipeline.local_bootstrap_smoke
if ($LASTEXITCODE -ne 0) {
    throw "Containerized publisher bootstrap smoke test failed with exit code $LASTEXITCODE"
}

if ($RunHostPythonSmoke) {
    if (-not $SkipPythonSync) {
        Write-Host "Phase 4/4: syncing the local Python environment from pyproject..."
        & $pythonExe -m pip install --no-cache-dir -e $repoRoot
        if ($LASTEXITCODE -ne 0) {
            throw "Local Python environment sync failed with exit code $LASTEXITCODE"
        }
    } else {
        Write-Host "Phase 4/4: running host Python smoke without syncing the local environment."
    }

    & $pythonExe -m unittest tests.integration.test_publisher_bootstrap_smoke -v
    if ($LASTEXITCODE -ne 0) {
        throw "Host Python publisher bootstrap smoke test failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Host "Phase 4/4: host Python smoke not requested."
}

Write-Host "Publisher bootstrap smoke test passed."
