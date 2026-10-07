# Crea la base de datos BazarNimal con bd/bazarnimal.sql usando las contraseñas de un archivo .env.
#
# Local (MySQL en esta máquina, usuario root):
#   .\scripts\setup_database.ps1
#
# Aiven (producción): usa los datos de conexión de la consola de Aiven y su certificado CA.
#   .\scripts\setup_database.ps1 -Remote -EnvFile .env.production `
#       -MysqlHost <host>.aivencloud.com -MysqlPort <puerto> -MysqlUser avnadmin -SslCa .\ca.pem
param(
    [string]$MysqlUser = "root",
    [string]$MysqlHost = "127.0.0.1",
    [int]$MysqlPort = 3306,
    [string]$EnvFile = ".env",
    [switch]$Remote,
    [string]$SslCa
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$root = Split-Path -Parent $PSScriptRoot
$envPath = if ([System.IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $root $EnvFile }
$sqlFile = Join-Path $root "bd\bazarnimal.sql"

if (-not (Get-Command mysql -ErrorAction SilentlyContinue)) {
    throw "No se encontró el comando mysql. Agrega 'C:\Program Files\MySQL\MySQL Server 8.0\bin' al PATH."
}
if (-not (Test-Path $envPath)) { throw "No existe $EnvFile." }
if ($Remote -and -not $SslCa) { throw "Con -Remote indica el certificado CA de Aiven con -SslCa <ruta>." }
if ($SslCa -and -not (Test-Path $SslCa)) { throw "No existe el certificado: $SslCa" }

$values = @{}
foreach ($line in Get-Content $envPath) {
    if ($line -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $values[$Matches[1]] = $Matches[2].Trim() }
}
foreach ($key in "DB_PASSWORD", "DB_MIGRATION_PASSWORD") {
    if (-not $values[$key]) { throw "Falta $key en $EnvFile" }
}

function Quote-Sql([string]$value) { "'" + $value.Replace("\", "\\").Replace("'", "''") + "'" }

$prelude = "SET @app_password = $(Quote-Sql $values['DB_PASSWORD']);`n" +
           "SET @migrator_password = $(Quote-Sql $values['DB_MIGRATION_PASSWORD']);`n" +
           "SET @remote = $(if ($Remote) { 1 } else { 0 });`n"
$script = $prelude + (Get-Content $sqlFile -Raw -Encoding UTF8)

$mysqlArgs = @("--default-character-set=utf8mb4", "-h", $MysqlHost, "-P", $MysqlPort, "-u", $MysqlUser, "-p")
if ($SslCa) { $mysqlArgs += @("--ssl-mode=VERIFY_IDENTITY", "--ssl-ca=$((Resolve-Path $SslCa).Path)") }

Write-Host "Ejecutando bd/bazarnimal.sql como $MysqlUser@$MysqlHost (te pedirá su contraseña)..."
$script | mysql @mysqlArgs
if ($LASTEXITCODE -ne 0) { throw "mysql terminó con error ($LASTEXITCODE)" }
Write-Host "Base de datos lista. Arranca el backend y se creará el administrador inicial."
