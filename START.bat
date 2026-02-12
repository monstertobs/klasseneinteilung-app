@echo off
chcp 65001 >nul 2>&1
cls
echo ========================================================
echo         Klasseneinteilung - App wird gestartet
echo ========================================================
echo.

REM Pruefe ob Installation durchgefuehrt wurde
if not exist venv (
    echo App wurde noch nicht installiert!
    echo.
    echo Bitte fuehren Sie zuerst "INSTALLATION.bat" aus.
    echo.
    pause
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
call venv\Scripts\activate.bat

REM Starte App
echo Starte Klasseneinteilung-App...
echo.
echo --------------------------------------------------------
echo   Die App laeuft jetzt!
echo.
echo   Browser oeffnet automatisch in 3 Sekunden...
echo   Falls nicht: http://localhost:5050
echo.
echo   Login:
echo     Benutzername: admin
echo     Passwort:     admin123
echo.
echo   Zum Beenden: Dieses Fenster schliessen oder Strg+C
echo --------------------------------------------------------
echo.

REM Warte 3 Sekunden
timeout /t 3 /nobreak >nul

REM Oeffne Browser
start http://localhost:5050

REM Starte Flask
python app.py
