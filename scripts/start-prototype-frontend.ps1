param([switch]$LocalPreview)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$previous = $env:NEXT_PUBLIC_DEV_AUTH_ENABLED
$previousBackend = $env:BACKEND_API_URL
$env:NEXT_PUBLIC_DEV_AUTH_ENABLED = if ($LocalPreview) { 'true' } else { 'false' }
$env:BACKEND_API_URL = 'http://127.0.0.1:8000'
Push-Location (Join-Path $repoRoot 'frontend')
try { npm run dev } finally {
    Pop-Location
    $env:NEXT_PUBLIC_DEV_AUTH_ENABLED = $previous
    $env:BACKEND_API_URL = $previousBackend
}
