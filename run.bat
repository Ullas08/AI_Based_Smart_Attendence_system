@echo off
echo ================================================
echo   AI-Based Smart Attendance System
echo   Starting up...
echo ================================================

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [INFO] No venv found - using system Python
)

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
)

echo [OK] Starting Flask server...
echo [INFO] Open browser at: http://127.0.0.1:5000
echo [INFO] Default login: admin / Admin@123
echo.
python app.py
pause
