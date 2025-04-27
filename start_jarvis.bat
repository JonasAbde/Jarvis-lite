@echo off
cls
color 0A
echo ====================================
echo JARVIS LITE - VERSIONSVÆLGER
echo ====================================
echo.
echo Velkommen til Jarvis Lite versionsvælgeren
echo.
echo Dette program lader dig køre de forskellige versioner af Jarvis
echo fra et centralt sted. Vælg en version for at starte.
echo.
echo [1] v1: Basis If/Else Version (tekstinput, enkel logik)
echo [2] v2: Dictionary Notebook Version (dictionary-baseret, Jupyter)
echo [3] v3: ML/TensorFlow Version (machine learning intentgenkendelse)
echo [4] v4: Eksamenspakke (komplet pakke med ML og dokumentation)
echo [Q] Afslut programmet
echo.

:MENU
SET /P VALG="Indtast dit valg (1-4 eller Q): "

IF /I "%VALG%"=="1" GOTO V1
IF /I "%VALG%"=="2" GOTO V2
IF /I "%VALG%"=="3" GOTO V3
IF /I "%VALG%"=="4" GOTO V4
IF /I "%VALG%"=="Q" GOTO AFSLUT
IF /I "%VALG%"=="q" GOTO AFSLUT

echo.
echo Ugyldigt valg. Prøv igen.
echo.
GOTO MENU

:V1
echo.
echo Starter Jarvis v1 (Basis If/Else Version)...
call jarvis_evolution\v1_basis_if_else\start_jarvis_v1.bat
GOTO AFSLUT

:V2
echo.
echo Starter Jarvis v2 (Dictionary Notebook Version)...
call jarvis_evolution\v2_dict_notebook\start_jarvis_v2.bat
GOTO AFSLUT

:V3
echo.
echo Starter Jarvis v3 (ML/TensorFlow Version)...
call jarvis_evolution\v3_ml_tensorflow\start_jarvis_v3.bat
GOTO AFSLUT

:V4
echo.
echo Starter Jarvis v4 (Eksamenspakke)...
call jarvis_evolution\v4_eksamen_komplet\start_jarvis.bat
GOTO AFSLUT

:AFSLUT
echo.
echo Tak for at bruge Jarvis Lite!
echo.
