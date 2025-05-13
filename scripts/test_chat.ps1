# Jarvis-Lite Chat Test Script
# --------------------------

# Aktiver virtuelt miljø
if (Test-Path -Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "❌ Virtuelt miljø ikke fundet. Kør setup_jarvis.ps1 først." -ForegroundColor Red
    exit
}

Write-Host "🧪 Starter test af Jarvis-Lite Chat-funktionalitet..." -ForegroundColor Cyan

# Tjek om de nødvendige filer findes
$requiredFiles = @(
    "src\api_server.py", 
    "src\static_server.py", 
    "src\static\index.html", 
    "src\static\app.js", 
    "src\static\style.css"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (!(Test-Path -Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Følgende filer mangler:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    Write-Host "`nKonfigurer chat-funktionaliteten først." -ForegroundColor Yellow
    exit
}

# Start API-server i en separat PowerShell
Write-Host "`n🚀 Starter API-server på port 8001..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\src'; uvicorn api_server:app --reload --host 127.0.0.1 --port 8001"

# Start Web-UI i en separat PowerShell
Write-Host "🚀 Starter Web-UI server på port 8080..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\src'; uvicorn static_server:app --reload --host 127.0.0.1 --port 8080"

# Vent et øjeblik for at serverne kan starte
Write-Host "⏳ Venter på serverne..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test API-forbindelse
Write-Host "`n🔍 Tester API-forbindelse..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/status" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API-server kører og svarer korrekt!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ API-server svarer med status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Kunne ikke forbinde til API-server: $_" -ForegroundColor Red
}

# Test Web-UI forbindelse
Write-Host "`n🔍 Tester Web-UI forbindelse..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Web-UI server kører og svarer korrekt!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Web-UI server svarer med status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Kunne ikke forbinde til Web-UI server: $_" -ForegroundColor Red
}

# Åbn webbrowser til Jarvis-UI
Write-Host "`n🌐 Åbner Jarvis-Lite UI i browser..." -ForegroundColor Green
Start-Process "http://localhost:8080"

Write-Host "`n🎯 Test færdig! Du kan nu interagere med Jarvis-Lite via chat-grænsefladen." -ForegroundColor Cyan
Write-Host "   Send beskeder og se om du får svar. Prøv både tekst og stemmeinput." -ForegroundColor Cyan
Write-Host "`n💡 For komplet funktionalitet skal du køre start_jarvis.ps1." -ForegroundColor Yellow 