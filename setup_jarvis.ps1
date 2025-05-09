# Jarvis-Lite Automatisk Opsætning
# ----------------------------

Write-Host "🤖 Jarvis-Lite Opsætning starter..." -ForegroundColor Cyan

# 1. Tjek om Git er installeret
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git er ikke installeret. Download og installer fra https://git-scm.com/download/win" -ForegroundColor Red
    exit
}

# 2. Tjek om Python 3.11 er installeret
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    if ($pythonVersion -match "Python 3.11") {
        $pythonCmd = "python"
    }
}
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonVersion = python3 --version
    if ($pythonVersion -match "Python 3.11") {
        $pythonCmd = "python3"
    }
}
if (!$pythonCmd) {
    Write-Host "❌ Python 3.11 er ikke installeret. Download og installer fra https://www.python.org/downloads/" -ForegroundColor Red
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
    "src\cache\tts"
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
Write-Host "1. Start MCP-serveren (i én terminal):" -ForegroundColor White
Write-Host "   cd mcp-server/python" -ForegroundColor Yellow
Write-Host "   uvicorn mcp_server:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor Yellow

Write-Host "`n2. Start Jarvis (i en anden terminal):" -ForegroundColor White
Write-Host "   $env:PYTHONPATH='src'; python src/jarvis_main.py" -ForegroundColor Yellow

Write-Host "`n🧪 Kør tests med:" -ForegroundColor White
Write-Host "   pytest tests/" -ForegroundColor Yellow

Write-Host "`n🔍 Hvis du møder problemer, se docs/TODO_MCP_Integration.md for en detaljeret tjekliste." -ForegroundColor Magenta 