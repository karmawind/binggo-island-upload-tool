@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo   Social Auto Upload - One-Click Start
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v found

where node >/dev/null 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo [OK] Node.js %%v found

if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv!
        pause
        exit /b 1
    )
    echo [OK] venv created
) else (
    echo [OK] venv exists
)

call .venv\Scripts\activate.bat

python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] pip install failed!
        pause
        exit /b 1
    )
    echo [OK] Python deps installed
) else (
    echo [OK] Python deps ready
)

python -c "from patchright.sync_api import sync_playwright" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Installing patchright chromium...
    python -m patchright install chromium
) else (
    echo [OK] patchright ready
)

if not exist "conf.py" (
    if exist "conf.example.py" (
        copy conf.example.py conf.py >/dev/null
        echo [OK] conf.py created
    ) else (
        echo [ERROR] conf.py not found!
        pause
        exit /b 1
    )
) else (
    echo [OK] conf.py exists
)

if not exist "db\database.db" (
    if exist "db\createTable.py" (
        python db\createTable.py
        echo [OK] Database initialized
    )
) else (
    echo [OK] Database exists
)

if not exist "imageFile" mkdir imageFile
if not exist "videoFile" mkdir videoFile
if not exist "cookiesFile" mkdir cookiesFile
if not exist "cookies" mkdir cookies
echo [OK] Directories ready

if not exist "sau_frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    cd sau_frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed!
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Frontend deps installed
) else (
    echo [OK] Frontend deps ready
)

echo.
echo [1/2] Starting backend on port 5409...
start "" cmd /k "title SAU Backend && call .venv\Scripts\activate.bat && python sau_backend.py"

echo [INFO] Waiting for backend...
set BACKEND_READY=0
for /L %%i in (1,1,15) do (
    if !BACKEND_READY! equ 0 (
        timeout /t 1 /nobreak >nul
        curl -s -o nul http://localhost:5409 2>nul
        if not errorlevel 1 (
            set BACKEND_READY=1
        )
    )
)
if !BACKEND_READY! equ 1 (
    echo [OK] Backend started
) else (
    echo [WARN] Backend may not have started. Check its window.
)

echo [2/2] Starting frontend on port 5173...
start "" cmd /k "title SAU Frontend && cd sau_frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   All services started!
echo   Backend:  http://localhost:5409
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173
echo.
pause
