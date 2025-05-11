# Jarvis-Lite PyAudio Fix Script
# --------------------------
# Dette script hjælper med at løse problemer med PyAudio og andre lydbiblioteker på Windows

# Aktiver virtuelt miljø
if (Test-Path -Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "[FEJL] Virtuelt miljø ikke fundet. Kør setup_jarvis.ps1 først." -ForegroundColor Red
    exit
}

Write-Host "[INFO] Prøver at fikse lydproblemer..." -ForegroundColor Cyan

# Tjek Python version
$pythonVersion = python --version
Write-Host "[INFO] Bruger Python: $pythonVersion" -ForegroundColor Yellow

# Sørg for at hjælpebiblioteker er installeret
Write-Host "[1] Installerer nødvendige hjælpeværktøjer..." -ForegroundColor Yellow
pip install --upgrade wheel setuptools

# Fjern eksisterende problematiske lydbiblioteker
Write-Host "[2] Fjerner eksisterende lydbiblioteker..." -ForegroundColor Yellow
pip uninstall -y pyaudio sounddevice soundfile playsound

# Installer lydbiblioteker igen med specifikke versioner
Write-Host "[3] Installerer pipwin til Windows-pakker..." -ForegroundColor Yellow
pip install pipwin

Write-Host "[4] Installerer sounddevice..." -ForegroundColor Yellow
pip install sounddevice

Write-Host "[5] Installerer soundfile..." -ForegroundColor Yellow
pip install soundfile

Write-Host "[6] Installerer playsound..." -ForegroundColor Yellow
# Specifik version af playsound der virker mere stabilt på Windows
pip install playsound==1.2.2 

# Forsøg med PyAudio fra pipwin først
Write-Host "[7] Installerer PyAudio via pipwin..." -ForegroundColor Yellow
pipwin install pyaudio

# Hvis PyAudio stadig giver problemer, prøv direkte fra PyPI
$pyaudioTest = python -c "try: import pyaudio; print('OK'); except ModuleNotFoundError: print('FEJL')"
if ($pyaudioTest -eq "FEJL") {
    Write-Host "[8] Pipwin-installation af PyAudio fejlede. Prøver direkte installation..." -ForegroundColor Yellow
    pip install pyaudio
}

# Endelig test
Write-Host "`n[TEST] Tester lydbiblioteksimport..." -ForegroundColor Cyan
python -c @"
try:
    import pyaudio
    print('[OK] PyAudio: OK')
except Exception as e:
    print(f'[FEJL] PyAudio: {e}')

try:
    import sounddevice
    print('[OK] Sounddevice: OK')
except Exception as e:
    print(f'[FEJL] Sounddevice: {e}')

try:
    import soundfile
    print('[OK] SoundFile: OK')
except Exception as e:
    print(f'[FEJL] SoundFile: {e}')

try:
    import playsound
    print('[OK] Playsound: OK')
except Exception as e:
    print(f'[FEJL] Playsound: {e}')
"@

Write-Host "`n[OK] Fixe-script afsluttet." -ForegroundColor Green
Write-Host "   Hvis der stadig er problemer, prøv at installere disse pakker manuelt eller kontakt udviklerne." -ForegroundColor Yellow 