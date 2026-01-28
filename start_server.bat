@echo off
chcp 65001 >nul
echo ========================================
echo MT5 Django REST API Server
echo ========================================
echo.

if not exist "db.sqlite3" (
    echo [1/2] Running database migrations...
    py manage.py migrate
    echo.
) else (
    echo [1/2] Database exists, skipping migration
    echo.
)

echo [2/2] Starting Django development server...
echo.
echo Server URL: http://localhost:8000
echo Swagger Docs: http://localhost:8000/swagger/
echo API Docs: API_DOCS.md
echo Test Script: py test_api.py
echo.
echo Press Ctrl+C to stop server
echo ========================================
echo.

py manage.py runserver 0.0.0.0:8000
