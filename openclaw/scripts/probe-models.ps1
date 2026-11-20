# Prueba con TU clave qué modelos de Google responden (200) y cuáles no tienen cuota (429).
# Hace una llamada mínima por modelo. No imprime la clave.
# Uso:  .\scripts\probe-models.ps1            (filtra flash|lite|gemma)
#       .\scripts\probe-models.ps1 -Pattern '.' (prueba todos los que soportan generateContent)
param([string]$Pattern = 'flash|lite|gemma')
. (Join-Path $PSScriptRoot 'load-env.ps1')
Import-DotEnv (Join-Path (Split-Path $PSScriptRoot -Parent) '.env') | Out-Null
$key = $env:LLM_API_KEY
if (-not $key) { $key = $env:GEMINI_API_KEY }
if (-not $key) { $key = $env:GOOGLE_API_KEY }
if (-not $key) { Write-Error 'No hay clave (LLM_API_KEY / GEMINI_API_KEY / GOOGLE_API_KEY).'; exit 1 }

$h = @{ 'x-goog-api-key' = $key }
$base = 'https://generativelanguage.googleapis.com/v1beta'
$models = (Invoke-RestMethod "$base/models?pageSize=200" -Headers $h).models |
    Where-Object { $_.supportedGenerationMethods -contains 'generateContent' -and $_.name -match $Pattern }

$body = '{"contents":[{"parts":[{"text":"ok"}]}],"generationConfig":{"maxOutputTokens":5}}'
foreach ($m in $models) {
    $id = $m.name -replace '^models/', ''
    try {
        Invoke-RestMethod -Method Post -Uri "$base/models/${id}:generateContent" `
            -Headers $h -ContentType 'application/json' -Body $body | Out-Null
        $status = 'OK'
    } catch {
        $status = "HTTP $([int]$_.Exception.Response.StatusCode)"
    }
    '{0,-48} {1}' -f $id, $status
}
Write-Host "`nOK = usable con tu clave. HTTP 429 = sin cuota para ese modelo. Poné el id en LLM_MODEL."
