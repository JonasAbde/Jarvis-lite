# Jarvis-Lite Automatisk Opsætning (Minimal Version)
# ---------------------------------------

# Opret virtuelt miljø
if (!(Test-Path -Path "venv")) {
    Write-Host "Opretter virtuelt miljø..."
    python -m venv venv
}

# Aktiver virtuelt miljø og installer afhængigheder
Write-Host "Aktiverer virtuelt miljø og installerer afhængigheder..."
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install uvicorn fastapi 

# Installer problematiske pakker
Write-Host "Installerer kritiske pakker..."
pip install --upgrade scikit-learn nltk joblib numpy sounddevice playsound==1.2.2 pyaudio

# Opret nødvendige mapper
$directories = @(
    "data\conversations",
    "data\speaker_models",
    "data\voices",
    "logs",
    "models",
    "src\cache\models",
    "src\cache\tts",
    "mcp-server\python",
    "src\static"
)

foreach ($dir in $directories) {
    if (!(Test-Path -Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Oprettet mappe: $dir"
    }
}

# Opret __init__.py i src/llm (løser import-fejl)
if (!(Test-Path -Path "src\llm\__init__.py")) {
    New-Item -ItemType File -Path "src\llm\__init__.py" -Force
    Write-Host "Oprettet src\llm\__init__.py"
}

Write-Host "Jarvis-Lite er opsat og klar til brug!"
Write-Host "Start systemet med: .\start_jarvis.ps1" 