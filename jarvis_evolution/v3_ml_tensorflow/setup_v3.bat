@echo off
echo ========================
echo Jarvis v3 ML Installation
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
echo Opretter virtuelt miljø i den nuværende mappe...
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

:: Installer nødvendige pakker
pip install tensorflow numpy gtts playsound==1.2.2

if %errorlevel% neq 0 (
    echo [FEJL] Kunne ikke installere pakker
    echo Tryk en tast for at afslutte...
    pause >nul
    exit /b 1
)

echo.
echo ========================
echo Installation færdig!
echo ========================
echo.
echo Du kan nu køre:
echo   start_jarvis_v3.bat
echo.
echo Tryk en tast for at afslutte...
pause >nul
