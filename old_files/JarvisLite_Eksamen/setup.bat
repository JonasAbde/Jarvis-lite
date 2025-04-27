@echo off
echo ========================
echo Jarvis Lite Installation
echo ========================
echo.

:: Tjek om Python er installeret
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEJL] Python ikke fundet. Installer venligst Python 3.9-3.11 fra python.org
    echo Tryk en tast for at afslutte...
    pause >nul
    exit /b 1
)

echo [OK] Python er installeret

:: Opret virtuelt miljø
echo Opretter virtuelt miljø...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [FEJL] Kunne ikke oprette virtuelt miljø
    echo Tryk en tast for at afslutte...
    pause >nul
    exit /b 1
)

:: Aktiverer miljøet og installerer pakker
echo Installerer pakker...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [FEJL] Kunne ikke installere pakker
    echo Tryk en tast for at afslutte...
    pause >nul
    exit /b 1
)

echo.
echo ============================
echo Installation gennemført!
echo ============================
echo.
echo Du kan nu:
echo 1) Køre 'start_jarvis.bat' for at starte Jarvis direkte
echo 2) Køre 'start_notebook.bat' for at åbne Jupyter Notebook
echo.
echo Tryk en tast for at afslutte...
pause >nul
