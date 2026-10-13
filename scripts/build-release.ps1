[CmdletBinding()]
param(
    [string]$Version = "0.1.0",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$dist = Join-Path $projectRoot "dist"
$build = Join-Path $projectRoot "build"

if (-not (Test-Path $python)) { throw "Python do ambiente virtual não encontrado: $python" }
if ($Clean) {
    Remove-Item -LiteralPath (Join-Path $dist "Manutec") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $build -Recurse -Force -ErrorAction SilentlyContinue
}

& $python -m PyInstaller --noconfirm --clean --distpath $dist --workpath $build (Join-Path $projectRoot "packaging\manutec.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou com código $LASTEXITCODE" }

$executable = Join-Path $dist "Manutec\Manutec.exe"
if (-not (Test-Path $executable)) { throw "Executável não produzido: $executable" }
Write-Host "Build Manutec $Version concluído em $executable" -ForegroundColor Green
