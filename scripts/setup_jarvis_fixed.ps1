# Jarvis-Lite Automatisk Opsætning
# ----------------------------

Write-Host "🤖 Jarvis-Lite Opsætning starter..." -ForegroundColor Cyan

# 1. Tjek om Git er installeret
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git er ikke installeret. Download og installer fra https://git-scm.com/download/win" -ForegroundColor Red
    exit
}

# 2. Tjek om Python 3.x er installeret
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    if ($pythonVersion -match "Python 3\.") {
        $pythonCmd = "python"
        Write-Host "✅ Fandt Python: $pythonVersion" -ForegroundColor Green
    }
}
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonVersion = python3 --version
    if ($pythonVersion -match "Python 3\.") {
        $pythonCmd = "python3"
        Write-Host "✅ Fandt Python: $pythonVersion" -ForegroundColor Green
    }
}
if (!$pythonCmd) {
    Write-Host "❌ Python 3.x er ikke installeret. Download og installer fra https://www.python.org/downloads/" -ForegroundColor Red
    exit
}

# 3. Klon eller opdater repository
$repoPath = $PWD.Path
$repoExists = Test-Path -Path "$repoPath\.git"

if (!$repoExists) {
    # Ikke i et git repo, så vi kloner
    Write-Host "🔄 Kloner Jarvis-Lite repository..." -ForegroundColor Yellow
    git clone https://github.com/JonasAbde/Jarvis-lite.git .
}
else {
    # Vi er i et git repo, så vi opdaterer
    Write-Host "🔄 Opdaterer Jarvis-Lite repository..." -ForegroundColor Yellow
    git pull
}

# 4. Opsæt/Opdater submodules
Write-Host "🔄 Initialiserer og opdaterer submoduler..." -ForegroundColor Yellow
git submodule update --init --recursive

# 5. Opret eller aktiver virtuelt miljø
if (!(Test-Path -Path "venv")) {
    Write-Host "🔧 Opretter virtuelt miljø..." -ForegroundColor Yellow
    & $pythonCmd -m venv venv
}

# 6. Aktiver virtuelt miljø og installer afhængigheder
Write-Host "🔧 Aktiverer virtuelt miljø og installerer afhængigheder..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install uvicorn fastapi # Sikrer at uvicorn er installeret

# Sørg for at specifikke problematiske pakker er installeret
Write-Host "🔧 Sikrer kritiske pakker er korrekt installeret..." -ForegroundColor Yellow
pip install --upgrade scikit-learn nltk joblib numpy sounddevice playsound==1.2.2 pyaudio

# 7. Opret nødvendige mapper og filer
Write-Host "🔧 Opretter nødvendige filer og mapper..." -ForegroundColor Yellow

# Opret __init__.py i src/llm (løser import-fejl)
if (!(Test-Path -Path "src\llm\__init__.py")) {
    New-Item -ItemType File -Path "src\llm\__init__.py" -Force
    Write-Host "✅ Oprettet src\llm\__init__.py" -ForegroundColor Green
}

# Opret data-mapper
$directories = @(
    "data\conversations",
    "data\speaker_models",
    "data\voices",
    "logs",
    "models",
    "src\cache\models",
    "src\cache\tts",
    "mcp-server\python", # Tilføj denne mappe, som mangler
    "src\static" # Tilføj static-mappen til web-UI
)

foreach ($dir in $directories) {
    if (!(Test-Path -Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "✅ Oprettet mappe: $dir" -ForegroundColor Green
    }
}

# 8. Information om at starte systemet
Write-Host "`n🚀 Jarvis-Lite er opsat og klar til brug!" -ForegroundColor Green
Write-Host "`n⚡ Sådan starter du systemet:" -ForegroundColor Cyan
Write-Host "1. Brug vores nye start-script:" -ForegroundColor White
Write-Host "   .\start_jarvis.ps1" -ForegroundColor Yellow
Write-Host "`n   Dette vil starte alt hvad der er nødvendigt, inklusiv" -ForegroundColor White
Write-Host "   - MCP-server på port 8000" -ForegroundColor White
Write-Host "   - API-server på port 8001" -ForegroundColor White
Write-Host "   - Web-UI på port 8080" -ForegroundColor White
Write-Host "   - Jarvis-kernefunktionalitet" -ForegroundColor White

Write-Host "`n🧪 Kør tests med:" -ForegroundColor White
Write-Host "   pytest tests/" -ForegroundColor Yellow

Write-Host "`n🔍 Hvis du møder problemer med lyd, prøv:" -ForegroundColor Magenta
Write-Host "   .\fix_pyaudio.ps1" -ForegroundColor Yellow 