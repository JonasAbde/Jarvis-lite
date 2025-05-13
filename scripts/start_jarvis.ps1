# Jarvis-Lite Start Script
# ---------------------

# Aktiver virtuelt miljø
if (Test-Path -Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "❌ Virtuelt miljø ikke fundet. Kør setup_jarvis.ps1 først." -ForegroundColor Red
    exit
}

# Tjek for nødvendige pakker
if (!(Get-Command uvicorn -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ uvicorn mangler. Installer pakker..." -ForegroundColor Yellow
    pip install uvicorn fastapi
}

# Tjek om PyAudio _portaudio kan importeres
Write-Host "🔍 Tjekker PyAudio installation..." -ForegroundColor Cyan
$pyaudioTest = python -c "try: import pyaudio._portaudio; print('OK'); except ModuleNotFoundError: print('FEJL')"
if ($pyaudioTest -eq "FEJL") {
    Write-Host "⚠️ PyAudio C-modulet mangler. Prøver at geninstallere..." -ForegroundColor Yellow
    Write-Host "💡 Du kan køre fix_pyaudio.ps1 for andre løsningsforslag." -ForegroundColor Yellow
    pip uninstall -y pyaudio
    pip install --force-reinstall pyaudio
}

# Tjek om __init__.py filen eksisterer
if (!(Test-Path -Path "src\llm\__init__.py")) {
    Write-Host "⚠️ src\llm\__init__.py mangler. Opretter..." -ForegroundColor Yellow
    New-Item -ItemType File -Path "src\llm\__init__.py" -Force
}

# Opret mcp-server/python hvis den ikke eksisterer
if (!(Test-Path -Path "mcp-server\python")) {
    Write-Host "⚠️ mcp-server\python mappe mangler. Opretter..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "mcp-server\python" -Force
    
    # Opret en simpel mcp_server.py fil
    $mcp_server_content = @"
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "MCP Server kører"}

@app.get("/status")
def get_status():
    return {"status": "online"}
"@
    $mcp_server_content | Out-File -FilePath "mcp-server\python\mcp_server.py" -Encoding utf8
    Write-Host "✅ Oprettet mcp_server.py med minimalt indhold" -ForegroundColor Green
}

# Tjek om static-mappen eksisterer
if (!(Test-Path -Path "src\static")) {
    Write-Host "⚠️ src\static mappe mangler. Opretter..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "src\static" -Force
}

# Check om alle nødvendige UI-filer eksisterer
$webfiles = @("index.html", "style.css", "app.js")
foreach ($file in $webfiles) {
    if (!(Test-Path -Path "src\static\$file")) {
        Write-Host "⚠️ src\static\$file mangler. Konfigurer web-UI'en først!" -ForegroundColor Yellow
    }
}

# Start MCP-server i en separat PowerShell
Write-Host "🚀 Starter MCP-server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\mcp-server\python'; uvicorn mcp_server:app --reload --host 127.0.0.1 --port 8000"

# Start API-server i en separat PowerShell
Write-Host "🚀 Starter Jarvis API-server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\src'; uvicorn api_server:app --reload --host 127.0.0.1 --port 8001"

# Start Web-UI i en separat PowerShell
Write-Host "🚀 Starter Jarvis Web-UI..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\src'; uvicorn static_server:app --reload --host 127.0.0.1 --port 8080"

# Vent et øjeblik for at serverne kan starte
Write-Host "⏳ Venter på serverne..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Åbn webbrowser til Jarvis-UI
Write-Host "🌐 Åbner Jarvis-Lite UI i browser..." -ForegroundColor Green
Start-Process "http://localhost:8080"

# Start Jarvis-Lite
Write-Host "🤖 Starter Jarvis-Lite kernefunktionalitet..." -ForegroundColor Green
$env:PYTHONPATH = "src"
python src/jarvis_main.py 