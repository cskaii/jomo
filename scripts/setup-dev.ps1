$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Install Node.js with npm first.' }
    if (-not (Test-Path backend/.venv/Scripts/python.exe)) {
        python -m venv backend/.venv
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ is required.' }
    }
    & backend/.venv/Scripts/python.exe -m ensurepip --upgrade
    & backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
    if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
    if (-not (Test-Path frontend/.env.local)) { Copy-Item frontend/.env.example frontend/.env.local }
    Push-Location frontend
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    } finally { Pop-Location }
    Write-Host 'Dependencies ready. See README.md for Supabase and local preview start commands.'
} finally { Pop-Location }
