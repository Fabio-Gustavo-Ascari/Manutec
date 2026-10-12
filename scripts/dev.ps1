param(
    [ValidateSet("test", "run", "validate")]
    [string]$Command = "test"
)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.13 -m venv .venv
}

$python = ".venv\Scripts\python.exe"
if ($Command -eq "test") {
    & $python -m pytest
} elseif ($Command -eq "run") {
    & $python -m assistencia_manager
} else {
    & "..\dev-harness\harness.ps1" validate -Project (Get-Location).Path -Profile python
}
