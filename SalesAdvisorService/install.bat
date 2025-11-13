@echo off
REM Installation script for Sales Advisor API
REM Compatible with Python 3.13 on Windows

echo ========================================
echo Sales Advisor API - Installation
echo ========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing dependencies from requirements.txt...
echo This may take a few minutes...
echo.
pip install -r requirements.txt

REM Check if installation was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Installation completed successfully!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Copy .env.template to .env
    echo 2. Fill in your Azure credentials in .env
    echo 3. Run: python start_api.py
    echo.
    echo See INSTALLATION_GUIDE.md for more details.
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ Installation failed!
    echo ========================================
    echo.
    echo Please try:
    echo 1. Run: python -m pip install --upgrade pip setuptools wheel
    echo 2. Run: pip install --only-binary :all: -r requirements.txt
    echo.
    echo See INSTALLATION_GUIDE.md for troubleshooting.
    echo.
)

pause

