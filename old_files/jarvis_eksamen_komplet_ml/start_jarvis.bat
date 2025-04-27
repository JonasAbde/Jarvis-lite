@echo off
echo ========================
echo Jarvis Lite Starter
echo ========================
echo.

:: Aktivér venv
call .venv\Scripts\activate.bat

:: Kør Jarvis
echo Starter Jarvis Lite...
python scripts\jarvis_lite.py

:: Pause hvis der er fejl
if %errorlevel% neq 0 (
    echo.
    echo [FEJL] Der skete en fejl under kørsel af Jarvis
    echo Tryk en tast for at afslutte...
    pause >nul
)
