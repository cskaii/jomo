param([ValidateRange(1, 65535)][int]$Port = 8000, [switch]$LocalPreview)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot 'backend'
$pythonPath = Join-Path $backendRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run scripts/setup-dev.ps1 first.'
}
$settings = @{ PYTHONPATH = $repoRoot; DEV_AUTH_ENABLED = 'false'; AUTO_SEED_CATALOG = 'false' }
if ($LocalPreview) {
    $localDatabase = (Join-Path $backendRoot 'jomo_local.db').Replace('\', '/')
    $settings.APP_ENV = 'development'
    $settings.DATABASE_URL = "sqlite:///$localDatabase"
    $settings.MIGRATION_DATABASE_URL = ''
    $settings.DEV_AUTH_ENABLED = 'true'
}
$previous = @{}
foreach ($name in $settings.Keys) {
    $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    [Environment]::SetEnvironmentVariable($name, $settings[$name], 'Process')
}
Push-Location $backendRoot
try {
    & $pythonPath -m app.db.setup --allow-sqlite
    if ($LASTEXITCODE -ne 0) { throw 'Database setup failed; the server was not started.' }
    & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port $Port
} finally {
    Pop-Location
    foreach ($name in $settings.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process')
    }
}
