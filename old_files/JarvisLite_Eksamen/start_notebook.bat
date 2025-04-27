@echo off
echo ========================
echo Jupyter Notebook Starter
echo ========================
echo.

:: Aktivér venv
call .venv\Scripts\activate.bat

:: Start Jupyter Notebook
echo Starter Jupyter Notebook...
jupyter notebook notebooks\Jarvis_Lite_Eksamen.ipynb

:: Pause hvis der er fejl
if %errorlevel% neq 0 (
    echo.
    echo [FEJL] Der skete en fejl under start af Jupyter Notebook
    echo Tryk en tast for at afslutte...
    pause >nul
)
