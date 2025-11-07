@echo off
title Discord Bot - Install Dependencies
color 0B

echo ================================================
echo    Discord Verification Bot
echo    Dependency Installer
echo ================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found!
echo [INFO] Installing dependencies...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo Please check your internet connection.
    pause
    exit /b 1
)

echo.
echo ================================================
echo [SUCCESS] All dependencies installed!
echo You can now run start_bot.bat
echo ================================================
echo.
pause
