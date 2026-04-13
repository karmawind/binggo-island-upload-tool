@echo off
chcp 65001 >nul 2>&1
title Social Auto Upload - Launcher
setlocal EnableDelayedExpansion

echo ========================================
echo   Social Auto Upload - One-Click Start
echo ========================================
echo.

:: ---------------------------------------------------
:: 1. 检查 Python
:: ---------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+ and add to PATH.
    echo         Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v found

:: ---------------------------------------------------
:: 2. 检查 Node.js
:: ---------------------------------------------------
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js LTS.
    echo         Download: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo [OK] Node.js %%v found

:: ---------------------------------------------------
:: 3. 检查/创建虚拟环境
:: ---------------------------------------------------
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found, creating...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

:: 激活虚拟环境
call .venv\Scripts\activate.bat

:: ---------------------------------------------------
:: 4. 检查/安装 Python 依赖
:: ---------------------------------------------------
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python dependencies not installed, running pip install...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies!
        pause
        exit /b 1
    )
    echo [OK] Python dependencies installed
) else (
    echo [OK] Python dependencies ready
)

:: ---------------------------------------------------
:: 5. 检查 patchright 浏览器驱动
:: ---------------------------------------------------
python -c "from patchright.sync_api import sync_playwright" >nul 2>&1
if errorlevel 1 (
    echo [WARN] patchright browser driver not installed, installing chromium...
    python -m patchright install chromium
    if errorlevel 1 (
        echo [WARN] Failed to install patchright browser driver. Login features may not work.
    ) else (
        echo [OK] patchright chromium installed
    )
) else (
    echo [OK] patchright ready
)

:: ---------------------------------------------------
:: 6. 检查 conf.py
:: ---------------------------------------------------
if not exist "conf.py" (
    if exist "conf.example.py" (
        echo [INFO] conf.py not found, copying from conf.example.py...
        copy conf.example.py conf.py >nul
        echo [OK] conf.py created from template
    ) else (
        echo [ERROR] conf.py and conf.example.py not found! Cannot start backend.
        pause
        exit /b 1
    )
) else (
    echo [OK] conf.py exists
)

:: ---------------------------------------------------
:: 7. 检查数据库
:: ---------------------------------------------------
if not exist "db\database.db" (
    echo [INFO] Database not found, initializing...
    if exist "db\createTable.py" (
        python db\createTable.py
        if errorlevel 1 (
            echo [ERROR] Failed to initialize database!
            pause
            exit /b 1
        )
        echo [OK] Database initialized
    ) else (
        echo [WARN] db\createTable.py not found, skipping database init
    )
) else (
    echo [OK] Database exists
)

:: ---------------------------------------------------
:: 8. 创建必要目录
:: ---------------------------------------------------
if not exist "imageFile" mkdir imageFile
if not exist "videoFile" mkdir videoFile
if not exist "cookiesFile" mkdir cookiesFile
if not exist "cookies" mkdir cookies
echo [OK] Directories ready

:: ---------------------------------------------------
:: 9. 检查端口占用
:: ---------------------------------------------------
netstat -ano | findstr ":5409 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port 5409 is already in use! Backend may fail to start.
    echo         You can close the process using it, or change the port in sau_backend.py
    echo.
    choice /c YN /m "Continue anyway? (Y/N)"
    if errorlevel 2 exit /b 0
)

netstat -ano | findstr ":5173 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port 5173 is already in use! Frontend may fail to start.
    choice /c YN /m "Continue anyway? (Y/N)"
    if errorlevel 2 exit /b 0
)

:: ---------------------------------------------------
:: 10. 检查/安装前端依赖
:: ---------------------------------------------------
if not exist "sau_frontend\node_modules" (
    echo [INFO] Frontend dependencies not found, running npm install...
    cd sau_frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies!
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies ready
)

:: ---------------------------------------------------
:: 11. 启动后端
:: ---------------------------------------------------
echo.
echo [1/2] Starting backend (port 5409)...
start "SAU Backend" cmd /k "call .venv\Scripts\activate.bat && python sau_backend.py"

:: 等待后端启动（最多等 15 秒）
echo [INFO] Waiting for backend to start...
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
    echo [OK] Backend started successfully
) else (
    echo [WARN] Backend may not have started. Check the Backend window for errors.
)

:: ---------------------------------------------------
:: 12. 启动前端
:: ---------------------------------------------------
echo [2/2] Starting frontend (port 5173)...
start "SAU Frontend" cmd /k "cd sau_frontend && npm run dev"

:: 等待前端启动
timeout /t 3 /nobreak >nul

:: ---------------------------------------------------
:: 完成
:: ---------------------------------------------------
echo.
echo ========================================
echo   All services started!
echo   Backend:  http://localhost:5409
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Opening browser in 2 seconds...
timeout /t 2 /nobreak >nul
start http://localhost:5173
echo.
echo This window can be safely closed.
pause
