# Jarvis-Lite Pakkereparation
# ---------------------------
# Dette script forsøger at reparere problemer med Python-pakker

# Aktiver virtuelt miljø
if (Test-Path -Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtuelt miljø ikke fundet. Kør setup_jarvis.ps1 først." -ForegroundColor Red
    exit
}

Write-Host "Forsøger at reparere pakkeproblemer..." -ForegroundColor Cyan

# Tjek Python version
$pythonVersion = python --version
Write-Host "Bruger Python: $pythonVersion" -ForegroundColor Yellow

# Afinstaller problematiske pakker
Write-Host "Afinstallerer problematiske pakker..." -ForegroundColor Yellow
pip uninstall -y numpy scikit-learn nltk regex

# Sørg for at hjælpebiblioteker er installeret
Write-Host "Installerer hjælpeværktøjer..." -ForegroundColor Yellow
pip install --upgrade pip setuptools wheel

# For at undgå source directory error - tjek om der findes en numpy mappe i projektet
if (Test-Path -Path "numpy") {
    Write-Host "!!! Der er en numpy mappe i projektet. Dette kan forårsage importproblemer!" -ForegroundColor Red
    Write-Host "Rename midlertidigt..." -ForegroundColor Yellow
    Rename-Item -Path "numpy" -NewName "numpy_old_temp"
}

# Installer wheel-versioner som er mere stabile
Write-Host "Installerer prebyggede pakker..." -ForegroundColor Yellow
pip install numpy==1.26.4 # Ældre, mere stabil version
pip install scikit-learn==1.4.1 # Ældre, mere stabil version
pip install nltk

# Opdater regex pakken
Write-Host "Installerer regex..." -ForegroundColor Yellow
pip install regex==2023.12.25 # Specifik version

# Gem oprindelig mappe
if (Test-Path -Path "numpy_old_temp") {
    Write-Host "Gendan numpy mappe..." -ForegroundColor Yellow
    Rename-Item -Path "numpy_old_temp" -NewName "numpy"
}

# Endelig test
Write-Host "Tester pakkeimports..." -ForegroundColor Cyan
python -c @"
try:
    import numpy
    print(f'NumPy: OK - version {numpy.__version__}')
except Exception as e:
    print(f'NumPy: FEJL - {str(e)}')

try:
    import sklearn
    print(f'Scikit-learn: OK - version {sklearn.__version__}')
except Exception as e:
    print(f'Scikit-learn: FEJL - {str(e)}')

try:
    import nltk
    print(f'NLTK: OK - version {nltk.__version__}')
except Exception as e:
    print(f'NLTK: FEJL - {str(e)}')

try:
    import regex
    print(f'Regex: OK - version {regex.__version__}')
except Exception as e:
    print(f'Regex: FEJL - {str(e)}')
"@

Write-Host "Pakkefikser afsluttet." -ForegroundColor Green
Write-Host "Prøv at køre 'python test_imports.py' for at teste alle moduler igen." -ForegroundColor Yellow 