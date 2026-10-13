[CmdletBinding()]
param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python do ambiente virtual não encontrado: $python" }

Push-Location $projectRoot
try {
    & $python -m compileall -q src
    if ($LASTEXITCODE -ne 0) { throw "Compilação Python falhou" }
    & $python -m assistencia_manager.infrastructure.release --project-root $projectRoot
    if ($LASTEXITCODE -ne 0) { throw "Gate de release falhou" }
    if ($Build) {
        & (Join-Path $projectRoot "scripts\build-release.ps1") -Clean
        if ($LASTEXITCODE -ne 0) { throw "Build final falhou" }
    }
} finally {
    Pop-Location
}
