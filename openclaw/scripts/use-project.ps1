# Activa el entorno del proyecto en la terminal ACTUAL. Usar con punto + espacio (dot-source):
#     . .\scripts\use-project.ps1
# Así `openclaw config ...`, `openclaw models ...` y `openclaw gateway run` apuntan a la
# config/estado del proyecto (TP_FINAL\openclaw) y NO a C:\home\.openclaw.
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot
. (Join-Path $PSScriptRoot 'load-env.ps1')

$env:OPENCLAW_STATE_DIR     = Join-Path $ProjectRoot '.openclaw'
$env:OPENCLAW_CONFIG_PATH   = Join-Path $ProjectRoot '.openclaw\openclaw.json'
$env:OPENCLAW_WORKSPACE_DIR = Join-Path $ProjectRoot 'workspace'

Write-Host "Cargando .env:"
Import-DotEnv (Join-Path $ProjectRoot '.env')
Write-Host "Config activa: $env:OPENCLAW_CONFIG_PATH"
