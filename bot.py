import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
from config_manager import config_manager
from logging_config import setup_logging

# --- Настройка логирования ---
setup_logging()
logger = logging.getLogger(f"glistbot.{__name__}")

# --- Загрузка конфигурации ---
try:
    config = config_manager.get_all()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Токен бота не найден в .env файле")
except (FileNotFoundError, ValueError) as e:
    logging.critical(f"Ошибка загрузки конфигурации: {e}")
    exit()

# --- Инициализация бота ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=config.get("BOT_PREFIX", "!"), intents=intents)

# --- Событие: бот готов ---
@bot.event
async def on_ready():
    logger.info(f'Бот {bot.user.name} успешно запущен и готов к работе!')
    logger.info(f'ID бота: {bot.user.id}')
    logger.info(f'Уровень верификации: {config.get("VERIFICATION_LEVEL")}')
    
    # Загрузка модулей (cogs)
    initial_extensions = ['verification_cog', 'stats_cog']
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'Модуль {extension} успешно загружен.')
        except Exception as e:
            logger.error(f'Ошибка при загрузке модуля {extension}: {e}', exc_info=True)

# --- Запуск бота ---
if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        logger.critical("Запуск невозможен: отсутствует токен бота.")
