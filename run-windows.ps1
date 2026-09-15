# Windows Startup Script for Housing Application (.NET Web Server)
$ErrorActionPreference = "Stop"

# Detect database and vault directories
$DefaultDb = "D:\areas_v11\organizer.db"
$DefaultAreas = "D:\areas_v11"

if (Test-Path $DefaultDb) {
    $DbPath = $DefaultDb
    $AreasRoot = $DefaultAreas
} elseif (Test-Path "$PSScriptRoot\organizer.db") {
    $DbPath = "$PSScriptRoot\organizer.db"
    $AreasRoot = "$PSScriptRoot\areas"
} else {
    $DbPath = $DefaultDb
    $AreasRoot = $DefaultAreas
}

$Port = 5000

# Get local LAN IPv4 address
$LocalIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*Tailscale*" -and $_.IPAddress -notlike "169.254.*" } |
    Select-Object -ExpandProperty IPAddress -First 1)

# Get Tailscale IP if connected
$TailscaleIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.InterfaceAlias -like "*Tailscale*" } |
    Select-Object -ExpandProperty IPAddress -First 1)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 🚀 Starting Housing Application .NET Web Server on Windows" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "📁 Database:    $DbPath" -ForegroundColor White
Write-Host "📂 Areas Root:  $AreasRoot" -ForegroundColor White
Write-Host "🌐 Local:       http://localhost:$Port" -ForegroundColor Green
if ($LocalIp) {
    Write-Host "📱 Network LAN: http://${LocalIp}:$Port  (Accessible to devices on your Wi-Fi/LAN)" -ForegroundColor Yellow
}
if ($TailscaleIp) {
    Write-Host "🔒 Tailscale:   http://${TailscaleIp}:$Port  (Accessible over Tailscale VPN)" -ForegroundColor Magenta
}
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor DarkGray

dotnet run --project "$PSScriptRoot\src\HousingApplication.Web\HousingApplication.Web.csproj" `
    --urls "http://0.0.0.0:$Port" `
    --ORGANIZER_DB_PATH "$DbPath" `
    --AREAS_ROOT_PATH "$AreasRoot"
