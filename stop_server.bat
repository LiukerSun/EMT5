@echo off
chcp 65001 >nul
echo ========================================
echo Stop MT5 Django REST API Server
echo ========================================
echo.

echo [1/2] Finding running Python processes...
echo.

REM Find process using port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    set PID=%%a
    goto :found
)

:found
if defined PID (
    echo Found process PID: %PID%
    echo.
    echo [2/2] Terminating process...
    taskkill /F /PID %PID%
    echo.
    echo Server stopped successfully
) else (
    echo No server found running on port 8000
)

echo.
echo ========================================
pause
