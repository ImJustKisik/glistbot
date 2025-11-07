@echo off
title Discord Bot - Verification System
color 0A

echo ================================================
echo    Discord Verification Bot
echo    Starting...
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

REM Проверка наличия .env файла
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please create .env file with your bot token.
    echo See .env.example for reference.
    echo.
    pause
    exit /b 1
)

REM Проверка наличия config.json
if not exist "config.json" (
    echo [ERROR] config.json not found!
    echo Please create config.json with your server settings.
    echo.
    pause
    exit /b 1
)

REM Проверка зависимостей
echo [INFO] Checking dependencies...
python -c "import discord" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] discord.py not installed!
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo [INFO] All checks passed!
echo [INFO] Starting bot...
echo.
echo ================================================
echo    Bot is running. Press Ctrl+C to stop.
echo ================================================
echo.

REM Запуск бота
python bot.py

REM Если бот остановился с ошибкой
if errorlevel 1 (
    echo.
    echo ================================================
    echo [ERROR] Bot stopped with error!
    echo Check the error message above.
    echo ================================================
    echo.
    pause
)
