import discord
from discord.ext import commands
import json
import os
import asyncio
from dotenv import load_dotenv

# --- Загрузка переменных окружения ---
load_dotenv()

# --- Загрузка конфигурации ---
if not os.path.exists('config.json'):
    raise FileNotFoundError("Файл 'config.json' не найден! Пожалуйста, создайте его.")

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# --- Настройка намерений (Intents) ---
# Боту нужны права для просмотра участников и сообщений.
intents = discord.Intents.default()
intents.members = True  # Для отслеживания входа новых участников
intents.message_content = True # Для обработки команд

# --- Инициализация бота ---
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Главная функция для асинхронной инициализации ---
async def main():
    # Загружаем модуль (Cog) с логикой верификации перед запуском
    try:
        await bot.load_extension('verification_cog')
        print('Модуль верификации загружен.')
    except Exception as e:
        print(f'Ошибка при загрузке модуля верификации: {e}')
        return

    # Получаем токен из переменных окружения
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Ошибка: Токен бота не найден в переменных окружения!")
        print("Создайте файл .env и добавьте строку: BOT_TOKEN=ваш_токен")
        return

    # Запускаем бота
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print("Ошибка: Неверный токен бота!")
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

# --- Событие при запуске ---
@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно запущен!')
    print(f'ID бота: {bot.user.id}')

# --- Глобальный обработчик ошибок команд ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У вас недостаточно прав для выполнения этой команды.", delete_after=10)
    elif isinstance(error, commands.CommandNotFound):
        # Игнорируем неизвестные команды
        pass
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Не хватает аргументов. Используйте: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`", delete_after=10)
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Неверный аргумент. Используйте: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`", delete_after=10)
    else:
        print(f"Ошибка в команде {ctx.command}: {error}")
        await ctx.send("❌ Произошла ошибка при выполнении команды.", delete_after=10)

# --- Запуск бота ---
if __name__ == "__main__":
    asyncio.run(main())
