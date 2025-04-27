@echo off
echo ========================
echo Jarvis Lite Starter
echo ========================
echo.

echo Aktiverer virtuelt miljø...
cd ..\..\
call .venv\Scripts\activate.bat
cd jarvis_evolution\v4_eksamen_komplet

echo Starter Jarvis Lite...
python scripts\jarvis_assistent.py

if %errorlevel% neq 0 (
    echo.
    echo [FEJL] Der skete en fejl under kørsel af Jarvis
    echo Tryk en tast for at afslutte...
    pause >nul
)

cd ..\..
call deactivate
