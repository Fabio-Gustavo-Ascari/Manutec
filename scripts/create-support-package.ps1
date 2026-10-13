[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path $env:TEMP "Manutec-support")
)

$ErrorActionPreference = "Stop"
$paths = Join-Path $env:LOCALAPPDATA "Manutec"
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmssZ")
$package = Join-Path $OutputDirectory "Manutec-support-$stamp"
New-Item -ItemType Directory -Path $package -Force | Out-Null

$diagnostics = [ordered]@{
    product = "Manutec"
    generated_utc = (Get-Date).ToUniversalTime().ToString("o")
    os = [Environment]::OSVersion.VersionString
    process_architecture = [Environment]::Is64BitProcess
    data_directory_exists = Test-Path (Join-Path $paths "data")
    log_directory_exists = Test-Path (Join-Path $paths "logs")
    backup_directory_exists = Test-Path (Join-Path $paths "backups")
    privacy = "No database, backup or raw log content is included."
}
$diagnostics | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $package "diagnostics.json") -Encoding UTF8
$archive = "$package.zip"
Compress-Archive -Path (Join-Path $package "*") -DestinationPath $archive -Force
Remove-Item -LiteralPath $package -Recurse -Force
Write-Host "Pacote sanitizado criado em $archive" -ForegroundColor Green
