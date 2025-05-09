# Jarvis-Lite Start Script
# ---------------------

# Aktiver virtuelt miljø
if (Test-Path -Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "❌ Virtuelt miljø ikke fundet. Kør setup_jarvis.ps1 først." -ForegroundColor Red
    exit
}

# Tjek om __init__.py filen eksisterer
if (!(Test-Path -Path "src\llm\__init__.py")) {
    Write-Host "⚠️ src\llm\__init__.py mangler. Opretter..." -ForegroundColor Yellow
    New-Item -ItemType File -Path "src\llm\__init__.py" -Force
}

# Start MCP-server i en separat PowerShell
Write-Host "🚀 Starter MCP-server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\mcp-server\python'; uvicorn mcp_server:app --reload --host 127.0.0.1 --port 8000"

# Vent et øjeblik for at MCP-serveren kan starte
Write-Host "⏳ Venter på MCP-server..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start Jarvis-Lite
Write-Host "🤖 Starter Jarvis-Lite..." -ForegroundColor Green
$env:PYTHONPATH = "src"
python src/jarvis_main.py 