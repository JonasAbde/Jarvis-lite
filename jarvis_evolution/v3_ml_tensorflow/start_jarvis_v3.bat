@echo off
echo ========================
echo Jarvis v3 - ML version
echo ========================
echo.

echo Aktiverer virtuelt miljø...
cd ..\..\
call .venv\Scripts\activate.bat
cd jarvis_evolution\v3_ml_tensorflow

echo Starter Jarvis v3 (TensorFlow ML)...
python jarvis_ml.py

if %errorlevel% neq 0 (
    echo.
    echo [FEJL] Der skete en fejl under kørsel af Jarvis
    echo Tryk en tast for at afslutte...
    pause >nul
)

cd ..\..
call deactivate
