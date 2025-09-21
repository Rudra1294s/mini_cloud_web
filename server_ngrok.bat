@echo off
REM -------------------------------
REM FastAPI + Ngrok + DuckDNS One-Click Starter
REM -------------------------------

REM Set your project path here
set PROJECT_PATH=C:\Users\Rudra.P.S\Documents\mini_cloud_web
cd /d "%PROJECT_PATH%"

REM -------------------------------
REM Start FastAPI server in background
REM -------------------------------
echo Starting FastAPI server...
start /b python server.py

REM Wait a few seconds for server to start
timeout /t 5

REM -------------------------------
REM Start ngrok in new window
REM -------------------------------
echo Starting ngrok...
start cmd /k "ngrok http 5000"

REM Wait a few seconds for ngrok to start
timeout /t 5

REM -------------------------------
REM Update DuckDNS with real public IP
REM -------------------------------
echo Updating DuckDNS...
python update_duckdns.py

echo.
echo -------------------------------
echo FastAPI + ngrok + DuckDNS started.
echo Check your DuckDNS domain for the global URL.
echo -------------------------------
pause
