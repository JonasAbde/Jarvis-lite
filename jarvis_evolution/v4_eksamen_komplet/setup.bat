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

:: Installer fra requirements.txt
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [FEJL] Kunne ikke installere pakker fra requirements.txt
    echo Tryk en tast for at afslutte...
    pause >nul
    exit /b 1
)

echo.
echo ========================
echo Installation færdig!
echo ========================
echo.
echo Jarvis Lite er nu klar til brug!
echo.
echo Kør Jarvis med:
echo   start_jarvis.bat
echo.
echo Eller start Jupyter Notebook med:
echo   start_notebook.bat
echo.
echo Tryk en tast for at afslutte...
pause >nul
