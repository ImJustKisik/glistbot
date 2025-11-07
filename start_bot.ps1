# Discord Verification Bot - Launcher
# Простой скрипт для запуска бота

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Discord Verification Bot" -ForegroundColor Green
Write-Host "   Starting..." -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия Python
Write-Host "[INFO] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Проверка наличия .env файла
Write-Host "[INFO] Checking .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file with your bot token." -ForegroundColor Red
    Write-Host "See .env.example for reference." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] .env file found" -ForegroundColor Green

# Проверка наличия config.json
Write-Host "[INFO] Checking config.json..." -ForegroundColor Yellow
if (-not (Test-Path "config.json")) {
    Write-Host "[ERROR] config.json not found!" -ForegroundColor Red
    Write-Host "Please create config.json with your server settings." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] config.json found" -ForegroundColor Green

# Проверка зависимостей
Write-Host "[INFO] Checking dependencies..." -ForegroundColor Yellow
$discordInstalled = python -c "import discord; import dotenv" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Some dependencies not installed!" -ForegroundColor Yellow
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host "[OK] All dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Bot is running. Press Ctrl+C to stop." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Запуск бота
try {
    python bot.py
} catch {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "[ERROR] Bot stopped with error!" -ForegroundColor Red
    Write-Host "Check the error message above." -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Если бот остановился нормально
Write-Host ""
Write-Host "[INFO] Bot stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
