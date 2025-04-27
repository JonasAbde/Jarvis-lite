@echo off
echo ========================
echo Jarvis v2 - Dictionary Notebook
echo ========================
echo.

echo Aktiverer virtuelt miljø...
cd ..\..\
call .venv\Scripts\activate.bat
cd jarvis_evolution\v2_dict_notebook

echo Starter Jarvis v2 (Dictionary Notebook)...
python -m jupyter notebook JarvisDict.ipynb

if %errorlevel% neq 0 (
    echo.
    echo [FEJL] Der skete en fejl under kørsel af Jupyter Notebook
    echo Tryk en tast for at afslutte...
    pause >nul
)

cd ..\..
call deactivate
