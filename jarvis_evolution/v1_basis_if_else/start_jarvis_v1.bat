@echo off
echo ========================
echo Jarvis v1 - Basis version
echo ========================
echo.

echo Aktiverer virtuelt miljø...
cd ..\..\
call .venv\Scripts\activate.bat
cd jarvis_evolution\v1_basis_if_else

echo Starter Jarvis v1 (If/Else)...
python jarvis_basis.py

if %errorlevel% neq 0 (
    echo.
    echo [FEJL] Der skete en fejl under kørsel af Jarvis
    echo Tryk en tast for at afslutte...
    pause >nul
)

cd ..\..
call deactivate
