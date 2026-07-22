@echo off
cd /d "%~dp0"
start "FFTA (servidor - cierra esta ventana para salir)" /min server.exe 8641
timeout /t 1 /nobreak >nul
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%EDGE%" (start "" "%EDGE%" --app=http://127.0.0.1:8641/ ^& exit /b)
if exist "%CHROME%" (start "" "%CHROME%" --app=http://127.0.0.1:8641/ ^& exit /b)
start "" http://127.0.0.1:8641/
