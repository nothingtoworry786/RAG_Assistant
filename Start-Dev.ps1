# Starts the FastAPI backend and Vite frontend in two separate PowerShell windows.
# Vite (frontend/vite.config.js) proxies /api to http://localhost:8000 — backend must use port 8000.
#
# Prerequisites: Node.js + npm in PATH; uv in PATH (https://docs.astral.sh/uv/).
# Run from repo root, or: powershell -File .\Start-Dev.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

if (-not (Test-Path (Join-Path $BackendDir "pyproject.toml"))) {
    Write-Error "Expected backend/pyproject.toml under: $Root"
}
if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    Write-Error "Expected frontend/package.json under: $Root"
}

$shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }

# Use `python -m uvicorn` (not `uv run uvicorn`) so uv does not use the Windows script trampoline,
# which can fail with "canonicalize script path" when the path contains spaces (e.g. Users\Yaali Madad\...).
Write-Host "Launching backend (uvicorn, http://127.0.0.1:8000) ..." -ForegroundColor Cyan
Start-Process -FilePath $shell -WorkingDirectory $BackendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    '$env:PORT = "8000"; uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload'
)

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies (npm install) ..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    try { npm install } finally { Pop-Location }
}

Start-Sleep -Seconds 2

Write-Host "Launching frontend (Vite) ..." -ForegroundColor Cyan
Start-Process -FilePath $shell -WorkingDirectory $FrontendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    "npm run dev"
)

Write-Host "Two windows were opened. Close each window to stop that server." -ForegroundColor Green
