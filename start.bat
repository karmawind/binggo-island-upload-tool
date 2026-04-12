@echo off
title Social Auto Upload

echo ========================================
echo   Social Auto Upload Launcher
echo ========================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv not found
    echo Run: python -m venv .venv
    pause
    exit /b 1
)

if not exist "sau_frontend\node_modules" (
    echo [INFO] Installing frontend deps...
    cd sau_frontend && npm install && cd ..
)

if not exist "imageFile" mkdir imageFile
if not exist "videoFile" mkdir videoFile
if not exist "cookiesFile" mkdir cookiesFile

echo [1/2] Starting backend (port 5409)...
start "Backend" cmd /k "call .venv\Scripts\activate.bat && python sau_backend.py"

echo [2/2] Starting frontend (port 5173)...
start "Frontend" cmd /k "cd sau_frontend && npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:5409
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Press any key to open browser...
pause >nul
start http://localhost:5173
