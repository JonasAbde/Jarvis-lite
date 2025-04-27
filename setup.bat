@echo off
color 0A
echo ====================================
echo JARVIS LITE - INSTALLATION
echo ====================================
echo.
echo Denne fil vil installere alle nødvendige komponenter
echo til at køre Jarvis Lite i alle versioner.
echo.
echo [1] Installér basis-pakker (minimal installation)
echo [2] Installér alle pakker inkl. TensorFlow (fuld installation)
echo [Q] Afslut uden installation
echo.

:MENU
SET /P VALG="Indtast dit valg (1, 2 eller Q): "

IF /I "%VALG%"=="1" GOTO BASIS
IF /I "%VALG%"=="2" GOTO FULD
IF /I "%VALG%"=="Q" GOTO AFSLUT
IF /I "%VALG%"=="q" GOTO AFSLUT

echo.
echo Ugyldigt valg. Prøv igen.
echo.
GOTO MENU

:BASIS
echo.
echo Opretter virtuelt miljø...
python -m venv .venv
call .venv\Scripts\activate.bat
echo Installerer basispakker (gTTS, playsound)...
pip install gtts==2.3.1 playsound==1.2.2
echo.
echo Basis installation færdig!
echo Du kan nu køre v1 og v2 versionerne.
echo.
pause
GOTO AFSLUT

:FULD
echo.
echo Opretter virtuelt miljø...
python -m venv .venv
call .venv\Scripts\activate.bat
echo Installerer alle pakker (inkl. TensorFlow)...
pip install gtts==2.3.1 playsound==1.2.2 tensorflow==2.16.2 numpy==1.24.3 jupyter
echo.
echo Fuld installation færdig!
echo Du kan nu køre alle versioner af Jarvis.
echo.
pause
GOTO AFSLUT

:AFSLUT
echo.
echo Installation afsluttet. Kør start_jarvis.bat for at starte Jarvis.
echo.
