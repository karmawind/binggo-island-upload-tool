@echo off
echo Starting Chrome with remote debugging port 9222...
echo.
echo NOTE: Close ALL Chrome windows before running this script!
echo.

taskkill /F /IM chrome.exe 2>nul
timeout /t 2 /nobreak >nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%~dp0chrome_debug_profile"

echo.
echo Chrome debug mode started on port 9222.
echo You can close this window.
pause
