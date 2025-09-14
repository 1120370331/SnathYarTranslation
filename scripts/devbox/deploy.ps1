Param()
$ErrorActionPreference = 'Stop'

$ROOT = Split-Path -Parent $PSCommandPath

Write-Host '[deploy] Backend'
& (Join-Path $ROOT 'deploy-backend.ps1')

Write-Host '[deploy] Frontend'
& (Join-Path $ROOT 'deploy-frontend.ps1')

Write-Host '[done] Deploy complete.'

