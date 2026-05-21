@echo off
REM GEOTA Dashboard Quick Start Script for Windows

echo.
echo ============================================
echo   GEOTA IT Park DSS - Quick Start
echo ============================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install packages
echo Installing required packages...
pip install -q -r requirements.txt

REM Run the app
echo.
echo ============================================
echo   Launching GEOTA Dashboard...
echo   Open browser: http://localhost:8501
echo ============================================
echo.

streamlit run app.py

pause
