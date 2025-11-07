# Copilot Instructions for glistbot

This document provides essential guidance for AI agents working on the `glistbot` codebase.

## 1. Project Overview & Architecture

This is a Python-based Discord bot for user verification, featuring a statistics module. The main goal is to protect servers from raids and provide analytics on member verification.

- **Main Entrypoint**: `bot.py` initializes the Discord bot, loads configuration, and loads the cogs (extensions).
- **Core Logic**: The application is split into "cogs," which are self-contained modules:
  - `verification_cog.py`: Manages all user verification logic. It supports three different verification levels, configurable in `config.json`.
  - `stats_cog.py`: Handles statistics and analytics. It uses an SQLite database (`verification_stats.db`) to log verification events and generate reports.
- **Configuration**:
  - `config.json`: Stores all operational parameters like Discord server/role/channel IDs and the current verification level. **This is the primary file for configuration.**
  - `.env`: Contains the secret `BOT_TOKEN`.
- **Database**:
  - An SQLite database `verification_stats.db` is used for all statistics.
  - The schema is defined and managed within `stats_cog.py`. Key tables include `verifications` and `moderator_actions`.

## 2. Developer Workflow

### Setup & Running the Bot

1.  **First-Time Setup**: Run `setup.bat`. This script creates the `.env` file from `.env.example` for you to add the bot token.
2.  **Install Dependencies**: Run `install_dependencies.bat`, which executes `pip install -r requirements.txt`.
3.  **Run the Bot**: Execute `start_bot.bat` or `start_bot.ps1`. These scripts run `python bot.py`.

### Testing

- The project uses Python's built-in `unittest` framework.
- The test file is `test_stats.py`, which focuses on testing the database logic in `stats_cog.py`.
- To run tests, execute the following command in the terminal:
  ```powershell
  python -m unittest test_stats.py
  ```

## 3. Code Conventions & Patterns

- **Cogs for Modularity**: All major features are implemented as cogs. When adding a new, distinct feature (e.g., moderation commands, games), create a new cog file and load it in `bot.py`.
- **Configuration Management**: All configuration values (except the bot token) are managed in `config.json`. The bot reads this file on startup. Do not hardcode IDs or settings.
- **Database Interaction**: All database operations are centralized in `stats_cog.py`. Use the methods in this cog to interact with the database rather than writing raw SQL queries in other parts of the code.
- **Error Handling**: The bot uses `try...except` blocks to handle common Discord API errors (e.g., `discord.Forbidden`, `discord.NotFound`) and provides user-friendly feedback.
- **Commands**: User-facing commands are created using the `@commands.command()` decorator from `discord.ext`. Ensure commands have clear names, help text, and appropriate permission checks (e.g., `@commands.has_permissions(administrator=True)`).
- **Logging**: The bot logs important events (like verifications) to a designated Discord channel specified in `config.json`. Use the `log_channel` for this purpose.


НЕ ПИШИ ЕБАНЫЕ MD ФАЙЛЫ ПО ПОВОДУ И БЕЗ