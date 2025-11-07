import discord
from discord.ext import commands
from discord.ui import View, Button, button
import random
import string
import urllib.parse
import os
from discord.utils import utcnow
from datetime import datetime, timedelta
from config_manager import config_manager

# --- Хранилище временных данных ---
# В реальном проекте лучше использовать базу данных (например, SQLite)
pending_verifications = {}

# --- Функция логирования верификаций ---
async def log_verification(bot, guild_id: int, member: discord.Member, status: str, method: str, moderator: discord.Member = None):
    """
    Логирует события верификации в специальный канал
    
    Параметры:
    - status: "успешно", "отклонено", "ошибка"
    - method: "команда", "qr-код", "модератор"
    - moderator: модератор (только для ручной верификации)
    """
    try:
        config = config_manager.get_all()
        log_channel_id = config.get("LOG_CHANNEL_ID")
        if not log_channel_id:
            return
        
        log_channel = bot.get_channel(log_channel_id)
        if not log_channel:
            return
        
        # Определяем цвет и эмодзи в зависимости от статуса
        if status == "успешно":
            color = discord.Color.green()
            emoji = "✅"
        elif status == "отклонено":
            color = discord.Color.red()
            emoji = "❌"
        else:
            color = discord.Color.orange()
            emoji = "⚠️"
        
        embed = discord.Embed(
            title=f"{emoji} Логирование верификации",
            color=color,
            timestamp=utcnow()
        )
        
        embed.add_field(name="Пользователь", value=f"{member.mention} ({member.name})", inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Статус", value=status.capitalize(), inline=True)
        embed.add_field(name="Метод", value=method.capitalize(), inline=True)
        embed.add_field(name="Уровень", value=str(config.get("VERIFICATION_LEVEL", "?")), inline=True)
        
        if moderator:
            embed.add_field(name="Модератор", value=moderator.mention, inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Аккаунт создан")
        embed.timestamp = member.created_at
        
        await log_channel.send(embed=embed)
        
    except Exception as e:
        print(f"Ошибка при логировании верификации: {e}")

# --- Класс для кнопок модерации ---
class ManualVerificationView(View):
    def __init__(self, member_id: int):
        super().__init__(timeout=86400)  # 24 часа на принятие решения
        # Динамически добавляем кнопки с уникальным custom_id
        self.add_item(Button(label="Одобрить", style=discord.ButtonStyle.green, custom_id=f"approve:{member_id}"))
        self.add_item(Button(label="Отклонить", style=discord.ButtonStyle.red, custom_id=f"deny:{member_id}"))

# --- Основной класс модуля (Cog) ---
class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def log_to_stats_db(self, user_id: int, username: str, guild_id: int, status: str, 
                        method: str, verification_level: int, moderator_id: int = None, 
                        moderator_name: str = None):
        """Вспомогательная функция для логирования в БД статистики"""
        try:
            stats_cog = self.bot.get_cog('StatsCog')
            if stats_cog:
                stats_cog.log_verification_to_db(user_id, username, guild_id, status, 
                                                method, verification_level, moderator_id, moderator_name)
        except Exception as e:
            print(f"Ошибка при логировании в статистику: {e}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")
        if not custom_id or ":" not in custom_id:
            return

        action, member_id_str = custom_id.split(":", 1)
        
        if action not in ["approve", "deny"]:
            return

        # Проверка прав модератора
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ У вас недостаточно прав для выполнения этого действия.", ephemeral=True)
            return
        
        try:
            member_id = int(member_id_str)
            member = interaction.guild.get_member(member_id)
        except (ValueError, AttributeError):
            await interaction.response.send_message("Не удалось обработать ID пользователя.", ephemeral=True)
            return

        if not member:
            await interaction.response.send_message(f"Пользователь с ID `{member_id}` не найден на сервере.", ephemeral=True)
            # Отключаем кнопки, так как пользователь ушел
            try:
                await interaction.message.edit(view=None)
            except (discord.NotFound, discord.HTTPException):
                pass
            return
            
        config = config_manager.get_all()

        if action == "approve":
            verified_role = interaction.guild.get_role(config["VERIFIED_ROLE_ID"])
            unverified_role = interaction.guild.get_role(config["UNVERIFIED_ROLE_ID"])

            if not verified_role or not unverified_role:
                await interaction.response.send_message("❌ Ошибка: Роли не найдены. Проверьте ID в конфиге.", ephemeral=True)
                return

            try:
                await member.add_roles(verified_role, reason=f"Одобрено модератором {interaction.user.name}")
                await member.remove_roles(unverified_role, reason="Верификация пройдена")
                await interaction.response.send_message(f"✅ Пользователь {member.mention} был одобрен.", ephemeral=True)

                await log_verification(self.bot, interaction.guild.id, member, "успешно", "модератор", interaction.user)
                self.log_to_stats_db(member.id, member.name, interaction.guild.id, "успешно", "модератор", config["VERIFICATION_LEVEL"], interaction.user.id, interaction.user.name)

                new_embed = interaction.message.embeds[0]
                new_embed.color = discord.Color.green()
                new_embed.description = f"**Статус: Одобрено**\nМодератор: {interaction.user.mention}"
                await interaction.message.edit(embed=new_embed, view=None)
            except discord.Forbidden:
                await interaction.response.send_message("❌ У бота недостаточно прав для изменения ролей.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.response.send_message(f"❌ Ошибка при изменении ролей: {e}", ephemeral=True)

        elif action == "deny":
            if not interaction.user.guild_permissions.kick_members:
                await interaction.response.send_message("❌ У вас недостаточно прав для кика пользователей.", ephemeral=True)
                return

            if member.guild_permissions.administrator:
                await interaction.response.send_message("❌ Нельзя кикнуть администратора.", ephemeral=True)
                return
            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message("❌ Нельзя кикнуть пользователя с ролью выше или равной роли бота.", ephemeral=True)
                return
            if member.id == interaction.client.user.id:
                await interaction.response.send_message("❌ Бота нельзя кикнуть самого себя.", ephemeral=True)
                return

            try:
                await member.kick(reason=f"Отклонено модератором {interaction.user.name}")
                await interaction.response.send_message(f"❌ Пользователь {member.mention} был кикнут.", ephemeral=True)

                await log_verification(self.bot, interaction.guild.id, member, "отклонено", "модератор", interaction.user)
                self.log_to_stats_db(member.id, member.name, interaction.guild.id, "отклонено", "модератор", config["VERIFICATION_LEVEL"], interaction.user.id, interaction.user.name)

                new_embed = interaction.message.embeds[0]
                new_embed.color = discord.Color.red()
                new_embed.description = f"**Статус: Отклонено (кик)**\nМодератор: {interaction.user.mention}"
                await interaction.message.edit(embed=new_embed, view=None)
            except discord.Forbidden:
                await interaction.response.send_message("❌ У бота недостаточно прав для кика этого пользователя.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.response.send_message(f"❌ Ошибка при кике: {e}", ephemeral=True)

    # --- Команда для смены уровня верификации ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlevel(self, ctx, level: int):
        if 1 <= level <= 3:
            config_manager.update_config("VERIFICATION_LEVEL", level)
            await ctx.send(f"✅ Уровень верификации изменен на **{level}**.")
        else:
            await ctx.send("❌ Неверный уровень. Пожалуйста, выберите от 1 до 3.")

    # --- Главное событие: новый пользователь на сервере ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = config_manager.get_all()
        unverified_role = member.guild.get_role(config["UNVERIFIED_ROLE_ID"])
        if unverified_role:
            try:
                await member.add_roles(unverified_role)
            except discord.Forbidden:
                print(f"Не удалось выдать роль 'Неверифицирован' пользователю {member.name}: недостаточно прав")
            except discord.HTTPException as e:
                print(f"Ошибка при выдаче роли пользователю {member.name}: {e}")

        level = config["VERIFICATION_LEVEL"]

        # --- Отправка приветственного сообщения ---
        welcome_channel_id = config.get("WELCOME_CHANNEL_ID")
        if welcome_channel_id:
            welcome_channel = self.bot.get_channel(welcome_channel_id)
            if welcome_channel:
                try:
                    # Формируем сообщение в зависимости от уровня
                    if level == 1:
                        instruction = f"Для получения доступа к серверу напишите команду `!verify` в этом канале."
                    elif level == 2:
                        instruction = f"Для получения доступа к серверу проверьте **личные сообщения** от меня. Я отправил вам QR-код с инструкциями.\n\n⚠️ Если ЛС не пришло — откройте личные сообщения от участников сервера в настройках конфиденциальности."
                    elif level == 3:
                        instruction = f"Ожидайте проверку модераторами. Это может занять некоторое время."
                    else:
                        instruction = "Следуйте инструкциям для верификации."

                    embed = discord.Embed(
                        title="👋 Добро пожаловать!",
                        description=f"Привет, {member.mention}! Добро пожаловать на сервер **{member.guild.name}**!",
                        color=discord.Color.blue(),
                        timestamp=utcnow()
                    )
                    embed.add_field(
                        name="🔐 Верификация",
                        value=instruction,
                        inline=False
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text=f"Уровень верификации: {level}")

                    await welcome_channel.send(embed=embed)
                except discord.Forbidden:
                    print(f"Не удалось отправить приветственное сообщение: недостаточно прав")
                except discord.HTTPException as e:
                    print(f"Ошибка при отправке приветственного сообщения: {e}")

        if level == 1:
            # Логика для уровня 1: простая команда
            # Приветственное сообщение уже отправлено выше
            pass
        elif level == 2:
            # Логика для уровня 2: QR-код
            token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            # Сохраняем токен и время его создания
            pending_verifications[member.id] = {
                "token": token,
                "timestamp": utcnow()
            }
            encoded_text = urllib.parse.quote(f"Ваш код: {token}")
            qr_url = f"https://quickchart.io/qr?text={encoded_text}&size=250"

            embed = discord.Embed(
                title="Верификация на сервере",
                description=f"Привет, {member.mention}! Чтобы получить доступ, отсканируйте QR-код и отправьте мне код командой `!code ВАШ_КОД`.",
                color=discord.Color.gold()
            )
            embed.set_image(url=qr_url)
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                print(f"Не удалось отправить ЛС пользователю {member.name}: личные сообщения закрыты")

        elif level == 3:
            # Логика для уровня 3: ручное одобрение
            mod_channel = self.bot.get_channel(config["MODERATOR_CHANNEL_ID"])
            if mod_channel:
                embed = discord.Embed(
                    title="Новый пользователь ожидает верификации",
                    description=f"Пользователь: {member.mention}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Дата регистрации", value=member.created_at.strftime("%d.%m.%Y %H:%M"))
                embed.set_footer(text=f"ID пользователя: {member.id}")

                try:
                    # Создаем View с ID пользователя для кнопок
                    await mod_channel.send(embed=embed, view=ManualVerificationView(member.id))
                except discord.Forbidden:
                    print(f"Не удалось отправить сообщение в канал модерации: недостаточно прав")
                except discord.HTTPException as e:
                    print(f"Ошибка при отправке в канал модерации: {e}")

    # --- Команды для верификации ---
    @commands.command()
    async def verify(self, ctx):
        # Только для уровня 1
        config = config_manager.get_all()

        if config["VERIFICATION_LEVEL"] != 1:
            return

        unverified_role = ctx.guild.get_role(config["UNVERIFIED_ROLE_ID"])
        verified_role = ctx.guild.get_role(config["VERIFIED_ROLE_ID"])

        if not unverified_role or not verified_role:
            await ctx.send("❌ Ошибка: Роли не найдены в конфигурации.", delete_after=5)
            return

        if unverified_role not in ctx.author.roles:
            await ctx.send("✅ Вы уже верифицированы!", delete_after=5)
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            return

        try:
            await ctx.author.remove_roles(unverified_role)
            await ctx.author.add_roles(verified_role)
            await ctx.send("✅ Вы успешно верифицированы!", delete_after=5)
            
            # Логирование
            await log_verification(
                bot=self.bot,
                guild_id=ctx.guild.id,
                member=ctx.author,
                status="успешно",
                method="команда"
            )
            
            # Логирование в БД статистики
            self.log_to_stats_db(
                user_id=ctx.author.id,
                username=ctx.author.name,
                guild_id=ctx.guild.id,
                status="успешно",
                method="команда",
                verification_level=config["VERIFICATION_LEVEL"]
            )
        except discord.Forbidden:
            await ctx.send("❌ У бота недостаточно прав для изменения ролей.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send("❌ Ошибка при верификации.", delete_after=5)
            print(f"Ошибка при верификации пользователя {ctx.author.name}: {e}")

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @commands.command()
    @commands.dm_only() # Команда работает только в ЛС
    async def code(self, ctx, provided_code: str):
        config = config_manager.get_all()

        if config["VERIFICATION_LEVEL"] != 2:
            return

        author_id = ctx.author.id
        verification_data = pending_verifications.get(author_id)

        if not verification_data:
            await ctx.send("❌ У вас нет активного кода верификации.")
            return

        # Проверка срока действия кода (15 минут)
        if utcnow() - verification_data["timestamp"] > timedelta(minutes=15):
            del pending_verifications[author_id]
            await ctx.send("❌ Ваш код верификации истек. Пожалуйста, запросите новый с помощью команды `!resendcode`.")
            return

        # Удаляем возможные спойлеры и лишние пробелы в введённом коде
        cleaned_input = provided_code.strip().replace('||', '')
        if verification_data["token"].lower() != cleaned_input.lower():
            await ctx.send("❌ Неверный код.")
            return

        del pending_verifications[author_id]

        guild = self.bot.get_guild(config["GUILD_ID"])
        if not guild:
            await ctx.send("❌ Не удалось найти сервер.")
            return

        member = guild.get_member(author_id)
        if not member:
            await ctx.send("❌ Не удалось найти вас на сервере. Попробуйте перезайти.")
            return

        verified_role = guild.get_role(config["VERIFIED_ROLE_ID"])
        unverified_role = guild.get_role(config["UNVERIFIED_ROLE_ID"])

        if not verified_role or not unverified_role:
            await ctx.send("❌ Ошибка: Роли не найдены на сервере.")
            return

        try:
            await member.add_roles(verified_role)
            await member.remove_roles(unverified_role)
            await ctx.send("✅ Верификация пройдена. Добро пожаловать!")
            
            # Логирование
            await log_verification(
                bot=self.bot,
                guild_id=guild.id,
                member=member,
                status="успешно",
                method="qr-код"
            )
            
            # Логирование в БД статистики
            self.log_to_stats_db(
                user_id=member.id,
                username=member.name,
                guild_id=guild.id,
                status="успешно",
                method="qr-код",
                verification_level=config["VERIFICATION_LEVEL"]
            )
        except discord.Forbidden:
            await ctx.send("❌ У бота недостаточно прав для изменения ролей.")
        except discord.HTTPException as e:
            await ctx.send("❌ Ошибка при верификации.")
            print(f"Ошибка при верификации пользователя {ctx.author.name}: {e}")

    @commands.command()
    @commands.dm_only() # Команда работает только в ЛС
    async def resendcode(self, ctx):
        """Повторная отправка QR-кода для верификации"""
        config = config_manager.get_all()

        if config["VERIFICATION_LEVEL"] != 2:
            await ctx.send("❌ Эта команда доступна только при уровне верификации 2 (QR-код).")
            return

        author_id = ctx.author.id
        guild = self.bot.get_guild(config["GUILD_ID"])
        
        if not guild:
            await ctx.send("❌ Не удалось найти сервер.")
            return

        member = guild.get_member(author_id)
        if not member:
            await ctx.send("❌ Вы не найдены на сервере.")
            return

        # Проверяем, есть ли у пользователя роль неверифицирован
        unverified_role = guild.get_role(config["UNVERIFIED_ROLE_ID"])
        if not unverified_role or unverified_role not in member.roles:
            await ctx.send("✅ Вы уже верифицированы! Код больше не нужен.")
            return

        # Генерируем новый код (или используем существующий)
        verification_data = pending_verifications.get(author_id)
        if verification_data and utcnow() - verification_data["timestamp"] < timedelta(minutes=15):
            token = verification_data["token"]
            message_text = "Вот ваш **существующий** код верификации (действителен еще несколько минут):"
        else:
            token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            pending_verifications[author_id] = {
                "token": token,
                "timestamp": utcnow()
            }
            message_text = "Вот ваш **новый** код верификации (действителен 15 минут):"

        # Создаём QR-код
        encoded_text = urllib.parse.quote(f"Ваш код: {token}")
        qr_url = f"https://quickchart.io/qr?text={encoded_text}&size=250"

        embed = discord.Embed(
            title="🔄 Повторная отправка кода",
            description=f"{message_text}\n\nВаш код: ||{token}||",
            color=discord.Color.gold()
        )
        embed.set_image(url=qr_url)
        embed.add_field(
            name="💡 Подсказка",
            value="После сканирования QR-кода отправьте мне код командой:\n`!code ВАШ_КОД`\nИли просто отправьте код как текст в этом чате.",
            inline=False
        )
        embed.set_footer(text="Код действителен 15 минут")

        try:
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Ошибка при отправке QR-кода: {e}")
            print(f"Ошибка при повторной отправке QR-кода пользователю {ctx.author.name}: {e}")


# --- Функция для загрузки Cog в основного бота ---
async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
