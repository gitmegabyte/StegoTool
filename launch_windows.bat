@echo off
cd /d "%~dp0"

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.
    pause
    exit /b 1
)

:: Install dependencies if needed (silent)
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo Installing Pillow...
    python -m pip install Pillow --quiet
)
python -c "from cryptography.fernet import Fernet" 2>nul
if errorlevel 1 (
    echo Installing cryptography...
    python -m pip install cryptography --quiet
)

:: Run the application SILENTLY (no terminal window)
cd src
start "" pythonw run.py
exit