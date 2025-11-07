"""
Скрипт для тестирования модуля статистики
Проверяет работу базы данных и основных функций
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = 'verification_stats.db'

def test_database():
    """Тестирует наличие и структуру базы данных"""
    print("🔍 Проверка базы данных...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных '{DB_PATH}' не найдена!")
        print("   Запустите бота хотя бы раз, чтобы создать БД.")
        return False
    
    print(f"✅ База данных '{DB_PATH}' найдена")
    
    # Проверяем структуру
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['verifications', 'verification_attempts', 'member_joins']
        
        print("\n📋 Таблицы в базе данных:")
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (отсутствует!)")
        
        # Проверяем количество записей
        print("\n📊 Количество записей:")
        
        cursor.execute("SELECT COUNT(*) FROM verifications")
        verif_count = cursor.fetchone()[0]
        print(f"   Верификации: {verif_count}")
        
        cursor.execute("SELECT COUNT(*) FROM verification_attempts")
        attempts_count = cursor.fetchone()[0]
        print(f"   Попытки: {attempts_count}")
        
        cursor.execute("SELECT COUNT(*) FROM member_joins")
        joins_count = cursor.fetchone()[0]
        print(f"   Присоединения: {joins_count}")
        
        # Показываем последние записи
        if verif_count > 0:
            print("\n📜 Последние 5 верификаций:")
            cursor.execute("""
                SELECT username, status, method, timestamp 
                FROM verifications 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            for row in cursor.fetchall():
                username, status, method, timestamp = row
                emoji = "✅" if status == "успешно" else "❌"
                print(f"   {emoji} {username} - {method} ({timestamp})")
        
        conn.close()
        print("\n✅ База данных в порядке!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")
        return False

def add_test_data():
    """Добавляет тестовые данные для демонстрации"""
    print("\n🧪 Добавление тестовых данных...")
    
    if not os.path.exists(DB_PATH):
        print("❌ База данных не существует. Сначала запустите бота!")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Добавляем тестовые верификации
        test_verifications = [
            (123456789, "TestUser1", 1000000000, "успешно", "команда", None, None, 1),
            (123456790, "TestUser2", 1000000000, "успешно", "qr-код", None, None, 2),
            (123456791, "TestUser3", 1000000000, "успешно", "модератор", 999999999, "ModUser", 3),
            (123456792, "TestUser4", 1000000000, "отклонено", "модератор", 999999999, "ModUser", 3),
        ]
        
        for data in test_verifications:
            cursor.execute("""
                INSERT INTO verifications 
                (user_id, username, guild_id, status, method, moderator_id, moderator_name, verification_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
        
        # Добавляем тестовые присоединения
        test_joins = [
            (123456789, "TestUser1", 1000000000, 45),
            (123456790, "TestUser2", 1000000000, 120),
            (123456791, "TestUser3", 1000000000, 3),
            (123456792, "TestUser4", 1000000000, 2),
        ]
        
        for data in test_joins:
            cursor.execute("""
                INSERT INTO member_joins (user_id, username, guild_id, account_age_days)
                VALUES (?, ?, ?, ?)
            """, data)
        
        conn.commit()
        conn.close()
        
        print("✅ Тестовые данные добавлены!")
        print("\nТеперь попробуйте команды:")
        print("   !stats")
        print("   !verifstats")
        print("   !recent")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении тестовых данных: {e}")
        return False

def show_statistics():
    """Показывает основную статистику из БД"""
    print("\n📊 Статистика из базы данных:")
    
    if not os.path.exists(DB_PATH):
        print("❌ База данных не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM verifications WHERE status = 'успешно'")
        successful = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM verifications WHERE status = 'отклонено'")
        rejected = cursor.fetchone()[0]
        
        total = successful + rejected
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"\n✅ Успешных верификаций: {successful}")
        print(f"❌ Отклоненных верификаций: {rejected}")
        print(f"📈 Процент успешности: {success_rate:.1f}%")
        
        # По методам
        cursor.execute("""
            SELECT method, COUNT(*) 
            FROM verifications 
            GROUP BY method
        """)
        
        print("\n📋 По методам:")
        for method, count in cursor.fetchall():
            print(f"   {method.capitalize()}: {count}")
        
        # Топ модераторов
        cursor.execute("""
            SELECT moderator_name, COUNT(*) as count 
            FROM verifications 
            WHERE moderator_id IS NOT NULL
            GROUP BY moderator_id
            ORDER BY count DESC
            LIMIT 5
        """)
        
        moderators = cursor.fetchall()
        if moderators:
            print("\n🏆 Топ модераторов:")
            for i, (name, count) in enumerate(moderators, 1):
                print(f"   {i}. {name}: {count} верификаций")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("🤖 Тестирование модуля статистики Discord бота")
    print("=" * 60)
    
    # Проверяем БД
    if not test_database():
        print("\n💡 Совет: Запустите бота хотя бы один раз для создания БД")
        return
    
    # Показываем статистику
    show_statistics()
    
    # Предлагаем добавить тестовые данные
    print("\n" + "=" * 60)
    response = input("\n❓ Хотите добавить тестовые данные? (y/n): ").lower()
    if response == 'y':
        add_test_data()
        print("\n📊 Обновленная статистика:")
        show_statistics()
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("=" * 60)

if __name__ == "__main__":
    main()
