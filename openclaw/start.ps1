# Levanta OpenClaw con la configuración del proyecto. No modifica config ni estado.
# Uso:  powershell -ExecutionPolicy Bypass -File .\start.ps1
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'scripts\use-project.ps1')

$required = 'LLM_BASE_URL', 'LLM_API_KEY', 'LLM_MODEL'
$missing  = $required | Where-Object { -not [Environment]::GetEnvironmentVariable($_, 'Process') }
if ($missing) { Write-Error "Faltan en .env: $($missing -join ', ')"; exit 1 }
Write-Host "LLM: $env:LLM_MODEL  @  $env:LLM_BASE_URL"

openclaw config validate
if ($LASTEXITCODE -ne 0) { Write-Error 'La config no valida; no se inicia el gateway.'; exit 1 }
openclaw gateway run
