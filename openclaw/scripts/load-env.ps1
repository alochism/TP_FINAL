# Carga un .env en el proceso actual SIN pisar variables ya definidas.
# Solo imprime NOMBRES de variables, nunca valores.
function Import-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { Write-Host "  (no hay .env en $Path)"; return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }
        $i = $line.IndexOf('=')
        if ($i -lt 1) { return }
        $name  = $line.Substring(0, $i).Trim()
        $value = $line.Substring($i + 1).Trim().Trim('"').Trim("'")
        if (-not [Environment]::GetEnvironmentVariable($name, 'Process')) {
            [Environment]::SetEnvironmentVariable($name, $value, 'Process')
            Write-Host "  cargada: $name"
        }
    }
}
