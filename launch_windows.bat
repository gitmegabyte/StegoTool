@echo off
setlocal

title StegoTool

REM ============================================================
REM StegoTool Launcher - Windows
REM ============================================================

set "ROOT_DIR=%~dp0"
set "APP_FILE=%ROOT_DIR%stegotool.pyw"

echo ========================================
echo              STEGOTOOL
echo ========================================
echo.
echo [INFO] Checking Python...

REM ------------------------------------------------------------
REM Check Python
REM ------------------------------------------------------------

where pythonw >nul 2>&1

if errorlevel 1 (
    where python >nul 2>&1

    if errorlevel 1 (
        echo.
        echo [ERROR] Python was not found.
        echo.
        echo Please install Python from:
        echo https://www.python.org/downloads/
        echo.
        echo Make sure Python is added to PATH.
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Python found.
echo.

REM ------------------------------------------------------------
REM Check application
REM ------------------------------------------------------------

if not exist "%APP_FILE%" (
    echo [ERROR] StegoTool application not found.
    echo.
    echo Expected:
    echo %APP_FILE%
    echo.
    pause
    exit /b 1
)

echo [OK] StegoTool application found.
echo.
echo [INFO] Starting StegoTool...
echo.

REM ------------------------------------------------------------
REM Launch application
REM ------------------------------------------------------------

where pythonw >nul 2>&1

if not errorlevel 1 (
    start "" pythonw "%APP_FILE%"
) else (
    start "" python "%APP_FILE%"
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start StegoTool.
    echo.
    pause
    exit /b 1
)

echo [OK] StegoTool started.
echo.

endlocal
exit /b 0