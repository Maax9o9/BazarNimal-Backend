# Crea la base de datos BazarNimal con bd/bazarnimal.sql usando las contraseñas del .env.
# Uso:  .\scripts\setup_database.ps1 [-MysqlUser root] [-MysqlHost 127.0.0.1]
param(
    [string]$MysqlUser = "root",
    [string]$MysqlHost = "127.0.0.1",
    [int]$MysqlPort = 3306
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
$sqlFile = Join-Path $root "bd\bazarnimal.sql"

if (-not (Test-Path $envFile)) { throw "No existe .env. Copia .env.example como .env y complétalo." }

$values = @{}
foreach ($line in Get-Content $envFile) {
    if ($line -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $values[$Matches[1]] = $Matches[2].Trim() }
}
foreach ($key in "DB_PASSWORD", "DB_MIGRATION_PASSWORD") {
    if (-not $values[$key]) { throw "Falta $key en .env" }
}

function Quote-Sql([string]$value) { "'" + $value.Replace("\", "\\").Replace("'", "''") + "'" }

$prelude = "SET @app_password = $(Quote-Sql $values['DB_PASSWORD']);`n" +
           "SET @migrator_password = $(Quote-Sql $values['DB_MIGRATION_PASSWORD']);`n"
$script = $prelude + (Get-Content $sqlFile -Raw -Encoding UTF8)

Write-Host "Ejecutando bd/bazarnimal.sql como $MysqlUser@$MysqlHost (te pedirá su contraseña)..."
$script | mysql --default-character-set=utf8mb4 -h $MysqlHost -P $MysqlPort -u $MysqlUser -p
if ($LASTEXITCODE -ne 0) { throw "mysql terminó con error ($LASTEXITCODE)" }
Write-Host "Base de datos lista. Arranca el backend y se creará el administrador inicial."
