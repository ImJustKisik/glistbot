import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta
from discord.utils import utcnow
from typing import Dict, List, Tuple
from config_manager import config_manager

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'verification_stats.db'
        self.init_database()

    def init_database(self):
        """Инициализация базы данных для хранения статистики"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для хранения верификаций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                method TEXT NOT NULL,
                moderator_id INTEGER,
                moderator_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                verification_level INTEGER
            )
        ''')
        
        # Таблица для хранения попыток верификации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для хранения информации о присоединениях
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS member_joins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                account_age_days INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # --- Индексы для ускорения запросов ---
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verif_guild_time ON verifications(guild_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verif_user ON verifications(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user ON verification_attempts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_member_joins_guild_time ON member_joins(guild_id, timestamp)")

        conn.commit()
        conn.close()

    def log_verification_to_db(self, user_id: int, username: str, guild_id: int, status: str, 
                               method: str, verification_level: int, moderator_id: int = None, 
                               moderator_name: str = None):
        """Записывает верификацию в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO verifications 
                (user_id, username, guild_id, status, method, moderator_id, moderator_name, verification_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, guild_id, status, method, moderator_id, moderator_name, verification_level))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при записи верификации в БД: {e}")

    def log_member_join(self, user_id: int, username: str, guild_id: int, account_age_days: int):
        """Записывает присоединение участника в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO member_joins (user_id, username, guild_id, account_age_days)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, guild_id, account_age_days))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при записи присоединения в БД: {e}")

    def log_verification_attempt(self, user_id: int, guild_id: int, success: bool):
        """Записывает попытку верификации"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO verification_attempts (user_id, guild_id, success)
                VALUES (?, ?, ?)
            ''', (user_id, guild_id, success))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при записи попытки верификации в БД: {e}")

    def get_stats_period(self, guild_id: int, days: int = 7) -> Dict:
        """Получает статистику за определенный период"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            date_threshold = utcnow() - timedelta(days=days)
            
            # Общее количество верификаций
            cursor.execute('''
                SELECT COUNT(*) FROM verifications 
                WHERE guild_id = ? AND timestamp > ?
            ''', (guild_id, date_threshold))
            total_verifications = cursor.fetchone()[0]
            
            # Успешные верификации
            cursor.execute('''
                SELECT COUNT(*) FROM verifications 
                WHERE guild_id = ? AND status = 'успешно' AND timestamp > ?
            ''', (guild_id, date_threshold))
            successful = cursor.fetchone()[0]
            
            # Отклоненные верификации
            cursor.execute('''
                SELECT COUNT(*) FROM verifications 
                WHERE guild_id = ? AND status = 'отклонено' AND timestamp > ?
            ''', (guild_id, date_threshold))
            rejected = cursor.fetchone()[0]
            
            # По методам
            cursor.execute('''
                SELECT method, COUNT(*) FROM verifications 
                WHERE guild_id = ? AND timestamp > ?
                GROUP BY method
            ''', (guild_id, date_threshold))
            by_method = dict(cursor.fetchall())
            
            # Новые участники
            cursor.execute('''
                SELECT COUNT(*) FROM member_joins 
                WHERE guild_id = ? AND timestamp > ?
            ''', (guild_id, date_threshold))
            new_members = cursor.fetchone()[0]
            
            # Средний возраст аккаунтов (в днях)
            cursor.execute('''
                SELECT AVG(account_age_days) FROM member_joins 
                WHERE guild_id = ? AND timestamp > ?
            ''', (guild_id, date_threshold))
            avg_account_age = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_verifications': total_verifications,
                'successful': successful,
                'rejected': rejected,
                'by_method': by_method,
                'new_members': new_members,
                'avg_account_age': round(avg_account_age, 1),
                'success_rate': round((successful / total_verifications * 100) if total_verifications > 0 else 0, 1)
            }
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {}

    def get_top_moderators(self, guild_id: int, limit: int = 5) -> List[Tuple]:
        """Получает топ модераторов по количеству верификаций"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT moderator_name, COUNT(*) as count 
                FROM verifications 
                WHERE guild_id = ? AND moderator_id IS NOT NULL
                GROUP BY moderator_id
                ORDER BY count DESC
                LIMIT ?
            ''', (guild_id, limit))
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"Ошибка при получении топа модераторов: {e}")
            return []

    def get_recent_verifications(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Получает последние верификации"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, status, method, timestamp 
                FROM verifications 
                WHERE guild_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (guild_id, limit))
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'username': r[0],
                    'status': r[1],
                    'method': r[2],
                    'timestamp': r[3]
                }
                for r in results
            ]
        except Exception as e:
            print(f"Ошибка при получении последних верификаций: {e}")
            return []

    @commands.command(name='stats')
    @commands.has_permissions(manage_guild=True)
    async def show_stats(self, ctx, days: int = 7):
        """
        Показывает общую статистику сервера
        
        Использование: !stats [дни]
        Пример: !stats 30 - статистика за последние 30 дней
        """
        if days < 1 or days > 365:
            await ctx.send("❌ Укажите количество дней от 1 до 365.")
            return

        stats = self.get_stats_period(ctx.guild.id, days)
        
        if not stats or stats['total_verifications'] == 0:
            await ctx.send(f"📊 За последние **{days} дней** нет данных о верификациях.")
            return

        # Создаем embed с общей статистикой
        embed = discord.Embed(
            title=f"📊 Статистика сервера {ctx.guild.name}",
            description=f"Данные за последние **{days} дней**",
            color=discord.Color.blue(),
            timestamp=utcnow()
        )

        # Общая информация
        embed.add_field(
            name="👥 Новые участники",
            value=f"```{stats['new_members']}```",
            inline=True
        )
        embed.add_field(
            name="✅ Верификации",
            value=f"```{stats['total_verifications']}```",
            inline=True
        )
        embed.add_field(
            name="📈 Успешность",
            value=f"```{stats['success_rate']}%```",
            inline=True
        )

        # Детали верификаций
        embed.add_field(
            name="✔️ Успешно",
            value=f"```{stats['successful']}```",
            inline=True
        )
        embed.add_field(
            name="❌ Отклонено",
            value=f"```{stats['rejected']}```",
            inline=True
        )
        embed.add_field(
            name="👤 Ср. возраст аккаунта",
            value=f"```{stats['avg_account_age']} дн.```",
            inline=True
        )

        # Методы верификации
        if stats['by_method']:
            methods_text = "\n".join([
                f"**{method.capitalize()}**: {count}" 
                for method, count in stats['by_method'].items()
            ])
            embed.add_field(
                name="📋 По методам верификации",
                value=methods_text or "Нет данных",
                inline=False
            )

        embed.set_footer(text=f"Запросил: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='verifstats', aliases=['vstats'])
    @commands.has_permissions(manage_guild=True)
    async def verification_stats(self, ctx):
        """
        Подробная статистика по верификациям
        
        Использование: !verifstats
        """
        stats_7d = self.get_stats_period(ctx.guild.id, 7)
        stats_30d = self.get_stats_period(ctx.guild.id, 30)
        top_mods = self.get_top_moderators(ctx.guild.id, 5)

        embed = discord.Embed(
            title="🔐 Статистика верификаций",
            description=f"Детальная информация по верификациям на сервере **{ctx.guild.name}**",
            color=discord.Color.gold(),
            timestamp=utcnow()
        )

        # Статистика за 7 дней
        if stats_7d and stats_7d['total_verifications'] > 0:
            embed.add_field(
                name="📅 За последние 7 дней",
                value=f"Всего: **{stats_7d['total_verifications']}**\n"
                      f"Успешно: **{stats_7d['successful']}** ({stats_7d['success_rate']}%)\n"
                      f"Отклонено: **{stats_7d['rejected']}**\n"
                      f"Новых участников: **{stats_7d['new_members']}**",
                inline=False
            )

        # Статистика за 30 дней
        if stats_30d and stats_30d['total_verifications'] > 0:
            embed.add_field(
                name="📅 За последние 30 дней",
                value=f"Всего: **{stats_30d['total_verifications']}**\n"
                      f"Успешно: **{stats_30d['successful']}** ({stats_30d['success_rate']}%)\n"
                      f"Отклонено: **{stats_30d['rejected']}**\n"
                      f"Новых участников: **{stats_30d['new_members']}**",
                inline=False
            )

        # Топ модераторов
        if top_mods:
            mods_text = "\n".join([
                f"**{i+1}.** {name}: {count} верификаций"
                for i, (name, count) in enumerate(top_mods)
            ])
            embed.add_field(
                name="🏆 Топ модераторов",
                value=mods_text,
                inline=False
            )

        # Текущая конфигурация
        level = config_manager.get("VERIFICATION_LEVEL", "?")
        embed.add_field(
            name="⚙️ Текущие настройки",
            value=f"Уровень верификации: **{level}**",
            inline=False
        )

        embed.set_footer(text=f"Запросил: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='recentverif', aliases=['recent'])
    @commands.has_permissions(manage_guild=True)
    async def recent_verifications(self, ctx, limit: int = 10):
        """
        Показывает последние верификации
        
        Использование: !recentverif [количество]
        Пример: !recentverif 15
        """
        if limit < 1 or limit > 25:
            await ctx.send("❌ Укажите количество от 1 до 25.")
            return

        recent = self.get_recent_verifications(ctx.guild.id, limit)
        
        if not recent:
            await ctx.send("📋 Нет данных о недавних верификациях.")
            return

        embed = discord.Embed(
            title=f"📋 Последние {len(recent)} верификаций",
            color=discord.Color.blue(),
            timestamp=utcnow()
        )

        for entry in recent:
            # Определяем эмодзи для статуса
            if entry['status'] == 'успешно':
                emoji = "✅"
                color_symbol = ""
            elif entry['status'] == 'отклонено':
                emoji = "❌"
                color_symbol = ""
            else:
                emoji = "⚠️"
                color_symbol = ""

            # Форматируем время
            try:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                time_str = timestamp.strftime("%d.%m.%Y %H:%M")
            except:
                time_str = entry['timestamp']

            embed.add_field(
                name=f"{emoji} {entry['username']}",
                value=f"Метод: **{entry['method'].capitalize()}**\n"
                      f"Время: {time_str}",
                inline=True
            )

        embed.set_footer(text=f"Запросил: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='checkuser', aliases=['userinfo'])
    @commands.has_permissions(manage_roles=True)
    async def check_user(self, ctx, member: discord.Member = None):
        """
        Проверяет информацию о пользователе
        
        Использование: !checkuser @пользователь
        """
        if not member:
            member = ctx.author

        # Получаем данные из БД
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Верификации пользователя
            cursor.execute('''
                SELECT status, method, timestamp FROM verifications 
                WHERE user_id = ? AND guild_id = ?
                ORDER BY timestamp DESC
                LIMIT 5
            ''', (member.id, ctx.guild.id))
            verifications = cursor.fetchall()
            
            # Попытки верификации
            cursor.execute('''
                SELECT COUNT(*) FROM verification_attempts 
                WHERE user_id = ? AND guild_id = ?
            ''', (member.id, ctx.guild.id))
            attempts = cursor.fetchone()[0]
            
            conn.close()
        except Exception as e:
            print(f"Ошибка при проверке пользователя: {e}")
            verifications = []
            attempts = 0

        # Создаем embed
        embed = discord.Embed(
            title=f"👤 Информация о пользователе",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue(),
            timestamp=utcnow()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Основная информация
        embed.add_field(
            name="Пользователь",
            value=f"{member.mention}\n`{member.name}`",
            inline=True
        )
        embed.add_field(
            name="ID",
            value=f"`{member.id}`",
            inline=True
        )
        embed.add_field(
            name="Никнейм",
            value=member.display_name,
            inline=True
        )

        # Даты
        account_age = (utcnow() - member.created_at).days
        join_age = (utcnow() - member.joined_at).days if member.joined_at else 0
        
        embed.add_field(
            name="Аккаунт создан",
            value=f"{member.created_at.strftime('%d.%m.%Y')}\n({account_age} дн. назад)",
            inline=True
        )
        embed.add_field(
            name="Присоединился",
            value=f"{member.joined_at.strftime('%d.%m.%Y') if member.joined_at else 'Неизвестно'}\n({join_age} дн. назад)",
            inline=True
        )
        embed.add_field(
            name="Попыток верификации",
            value=f"`{attempts}`",
            inline=True
        )

        # Роли
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        embed.add_field(
            name=f"Роли ({len(roles)})",
            value=" ".join(roles) if roles else "Нет ролей",
            inline=False
        )

        # История верификаций
        if verifications:
            verif_text = "\n".join([
                f"{'✅' if v[0] == 'успешно' else '❌'} {v[1].capitalize()} - {v[2][:10]}"
                for v in verifications
            ])
            embed.add_field(
                name="📜 История верификаций",
                value=verif_text,
                inline=False
            )

        # Предупреждения
        warnings = []
        if account_age < 7:
            warnings.append("⚠️ Аккаунт младше 7 дней")
        if account_age < 30:
            warnings.append("⚠️ Аккаунт младше месяца")
        if not member.avatar:
            warnings.append("⚠️ Нет аватара")
        
        if warnings:
            embed.add_field(
                name="⚠️ Предупреждения",
                value="\n".join(warnings),
                inline=False
            )

        embed.set_footer(text=f"Запросил: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Автоматически логирует присоединение участника"""
        account_age = (utcnow() - member.created_at).days
        self.log_member_join(member.id, member.name, member.guild.id, account_age)

# --- Функция для загрузки Cog ---
async def setup(bot):
    await bot.add_cog(StatsCog(bot))
