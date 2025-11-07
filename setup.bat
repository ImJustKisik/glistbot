@echo off
title Discord Bot - First Time Setup
color 0E

echo ================================================
echo    Discord Verification Bot
echo    First Time Setup Wizard
echo ================================================
echo.

REM Проверка Python
echo Step 1: Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)
echo [OK] Python is installed
echo.

REM Установка зависимостей
echo Step 2: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Проверка .env
echo Step 3: Checking .env file...
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Creating .env from template...
    copy .env.example .env >nul
    echo.
    echo [ACTION REQUIRED] Please edit .env file and add your bot token!
    echo File location: %cd%\.env
    echo.
    echo Press any key to open .env in Notepad...
    pause >nul
    notepad .env
)
echo [OK] .env file exists
echo.

REM Проверка config.json
echo Step 4: Checking config.json...
if not exist "config.json" (
    echo [ERROR] config.json not found!
    echo.
    echo Please create config.json with your server settings.
    echo See README.md for instructions.
    pause
    exit /b 1
)
echo [OK] config.json exists
echo.

echo ================================================
echo [SUCCESS] Setup completed!
echo.
echo Next steps:
echo 1. Make sure you edited .env with your bot token
echo 2. Update config.json with your server IDs
echo 3. Enable required intents in Discord Developer Portal:
echo    - Server Members Intent
echo    - Message Content Intent
echo 4. Double-click start_bot.bat to run the bot
echo ================================================
echo.
pause
