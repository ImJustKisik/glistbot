# 🖥️ Развертывание бота на выделенном сервере

Руководство по установке Discord бота на VPS/выделенный сервер (Ubuntu/Debian, Windows Server, или другие платформы).

---

## 📋 Содержание

1. [Выбор сервера](#выбор-сервера)
2. [Ubuntu/Debian Linux](#ubuntudebian-linux)
3. [Windows Server](#windows-server)
4. [Docker (универсально)](#docker-универсально)
5. [Автозапуск и мониторинг](#автозапуск-и-мониторинг)
6. [Безопасность](#безопасность)
7. [Обслуживание](#обслуживание)

---

## Выбор сервера

### Минимальные требования:
- **CPU:** 1 ядро
- **RAM:** 512 MB (рекомендуется 1 GB)
- **Диск:** 5 GB
- **Сеть:** Постоянное подключение к интернету
- **ОС:** Ubuntu 20.04+, Debian 11+, Windows Server 2019+

### Рекомендуемые провайдеры:
- **DigitalOcean** - от $4/мес (droplet 512MB)
- **Vultr** - от $3.50/мес
- **Hetzner** - от €4/мес
- **Linode** - от $5/мес
- **Contabo** - от €4/мес

---

## Ubuntu/Debian Linux

### Шаг 1: Подключение к серверу

```bash
# Подключитесь по SSH
ssh root@ваш_ip_адрес

# Или с указанием пользователя
ssh username@ваш_ip_адрес
```

### Шаг 2: Обновление системы

```bash
# Обновите список пакетов
sudo apt update

# Обновите систему
sudo apt upgrade -y
```

### Шаг 3: Установка Python

```bash
# Установите Python 3.11 (или новее)
sudo apt install python3.11 python3.11-venv python3-pip -y

# Проверьте версию
python3.11 --version
```

**Если Python 3.11 недоступен:**
```bash
# Добавьте PPA для новых версий Python
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

### Шаг 4: Создание пользователя для бота (безопасность)

```bash
# Создайте отдельного пользователя
sudo adduser discordbot

# Переключитесь на этого пользователя
sudo su - discordbot
```

### Шаг 5: Загрузка файлов бота

**Вариант А: Через Git (рекомендуется)**
```bash
# Установите git (если еще нет)
sudo apt install git -y

# Клонируйте репозиторий (если бот в Git)
git clone https://github.com/ваш_репозиторий/dbot.git
cd dbot
```

**Вариант Б: Загрузка архива**
```bash
# С локального компьютера используйте SCP
# На локальной машине выполните:
scp -r /path/to/dbot username@ваш_ip:/home/discordbot/

# Или используйте FileZilla/WinSCP для GUI загрузки
```

**Вариант В: Прямая загрузка на сервере**
```bash
# Создайте директорию
mkdir -p ~/discord-bot
cd ~/discord-bot

# Загрузите файлы (если у вас есть прямая ссылка)
wget https://example.com/bot.zip
unzip bot.zip
```

### Шаг 6: Настройка виртуального окружения

```bash
# Перейдите в папку сботом
cd ~/dbot

# Создайте виртуальное окружение
python3.11 -m venv venv

# Активируйте окружение
source venv/bin/activate

# Обновите pip
pip install --upgrade pip
```

### Шаг 7: Установка зависимостей

```bash
# Установите зависимости
pip install -r requirements.txt

# Если есть проблемы с aiohttp, установите build-tools
sudo apt install build-essential libffi-dev -y
```

### Шаг 8: Настройка .env

```bash
# Создайте .env файл
nano .env

# Добавьте ваш токен:
BOT_TOKEN=ваш_настоящий_токен_бота

# Сохраните: Ctrl+O, Enter, Ctrl+X
```

### Шаг 9: Настройка config.json

```bash
# Откройте config.json
nano config.json

# Замените все ID на ваши
# Сохраните: Ctrl+O, Enter, Ctrl+X
```

### Шаг 10: Тестовый запуск

```bash
# Активируйте окружение (если ещё не активно)
source venv/bin/activate

# Запустите бота
python bot.py

# Если всё работает, увидите:
# Бот TestBot успешно запущен!
# Модуль верификации загружен.

# Остановите: Ctrl+C
```

---

## Автозапуск и мониторинг

### Вариант 1: systemd (рекомендуется для Linux)

#### Создайте systemd service:

```bash
# Выйдите из пользователя discordbot
exit

# Создайте service файл
sudo nano /etc/systemd/system/discordbot.service
```

**Содержимое файла:**
```ini
[Unit]
Description=Discord Verification Bot
After=network.target

[Service]
Type=simple
User=discordbot
WorkingDirectory=/home/discordbot/dbot
Environment="PATH=/home/discordbot/dbot/venv/bin"
ExecStart=/home/discordbot/dbot/venv/bin/python /home/discordbot/dbot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Активируйте service:**
```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable discordbot

# Запустите бота
sudo systemctl start discordbot

# Проверьте статус
sudo systemctl status discordbot

# Просмотр логов
sudo journalctl -u discordbot -f
```

**Полезные команды:**
```bash
# Остановить бота
sudo systemctl stop discordbot

# Перезапустить бота
sudo systemctl restart discordbot

# Отключить автозапуск
sudo systemctl disable discordbot

# Посмотреть последние 100 строк логов
sudo journalctl -u discordbot -n 100
```

---

### Вариант 2: Screen (простой способ)

```bash
# Установите screen
sudo apt install screen -y

# Создайте новую screen сессию
screen -S discordbot

# Активируйте venv и запустите бота
cd ~/dbot
source venv/bin/activate
python bot.py

# Отключитесь от сессии: Ctrl+A, затем D

# Вернуться к сессии:
screen -r discordbot

# Посмотреть все сессии:
screen -ls

# Убить сессию:
screen -X -S discordbot quit
```

---

### Вариант 3: PM2 (Node.js менеджер процессов)

```bash
# Установите Node.js и npm
sudo apt install nodejs npm -y

# Установите PM2
sudo npm install -g pm2

# Создайте ecosystem файл
cd ~/dbot
nano ecosystem.config.js
```

**Содержимое ecosystem.config.js:**
```javascript
module.exports = {
  apps: [{
    name: 'discord-bot',
    script: 'venv/bin/python',
    args: 'bot.py',
    cwd: '/home/discordbot/dbot',
    interpreter: 'none',
    autorestart: true,
    watch: false,
    max_memory_restart: '200M',
    env: {
      NODE_ENV: 'production'
    }
  }]
}
```

**Запуск через PM2:**
```bash
# Запустите бота
pm2 start ecosystem.config.js

# Автозапуск при перезагрузке сервера
pm2 startup
pm2 save

# Полезные команды PM2
pm2 status           # Статус всех процессов
pm2 logs discord-bot # Логи бота
pm2 restart discord-bot # Перезапуск
pm2 stop discord-bot    # Остановка
pm2 delete discord-bot  # Удаление
pm2 monit            # Мониторинг в реальном времени
```

---

## Windows Server

### Шаг 1: Подключение

```powershell
# Подключитесь через Remote Desktop (RDP)
# IP: ваш_ip_адрес
# Пользователь: Administrator
```

### Шаг 2: Установка Python

1. Скачайте Python 3.11+ с [python.org](https://www.python.org/downloads/windows/)
2. Запустите установщик
3. ✅ Галочка "Add Python to PATH"
4. Установите

### Шаг 3: Загрузка файлов

- Скопируйте папку `dbot` на сервер через RDP
- Или используйте FileZilla/WinSCP

### Шаг 4: Установка зависимостей

```powershell
cd C:\path\to\dbot
pip install -r requirements.txt
```

### Шаг 5: Настройка .env и config.json

Отредактируйте файлы в Notepad

### Шаг 6: Создание Windows Service

**Используйте NSSM (Non-Sucking Service Manager):**

```powershell
# Скачайте NSSM
# https://nssm.cc/download

# Распакуйте и запустите
nssm.exe install DiscordBot

# В GUI укажите:
# Path: C:\Python311\python.exe
# Startup directory: C:\path\to\dbot
# Arguments: bot.py

# Запустите сервис
nssm.exe start DiscordBot

# Управление сервисом
nssm.exe stop DiscordBot
nssm.exe restart DiscordBot
nssm.exe remove DiscordBot
```

**Или используйте Task Scheduler:**
1. Откройте Task Scheduler
2. Create Task → "Discord Bot"
3. Trigger: At system startup
4. Action: Start program → `python.exe`
5. Arguments: `C:\path\to\dbot\bot.py`
6. Start in: `C:\path\to\dbot`

---

## Docker (универсально)

### Создайте Dockerfile

```dockerfile
# В папке с ботом создайте файл: Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов бота
COPY . .

# Запуск бота
CMD ["python", "bot.py"]
```

### Создайте docker-compose.yml

```yaml
version: '3.8'

services:
  discordbot:
    build: .
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./config.json:/app/config.json:ro
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Запуск через Docker

```bash
# Установите Docker (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установите Docker Compose
sudo apt install docker-compose -y

# Соберите и запустите
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Обновление после изменений
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Безопасность

### 1. Настройка файрвола (UFW на Ubuntu)

```bash
# Включите UFW
sudo ufw enable

# Разрешите SSH
sudo ufw allow 22/tcp

# Проверьте статус
sudo ufw status
```

### 2. Защита файлов

```bash
# Ограничьте права на .env
chmod 600 .env

# Только владелец может читать config.json
chmod 600 config.json

# Убедитесь, что файлы принадлежат правильному пользователю
sudo chown -R discordbot:discordbot ~/dbot
```

### 3. Регулярные обновления

```bash
# Обновляйте систему еженедельно
sudo apt update && sudo apt upgrade -y

# Обновляйте зависимости Python
pip install --upgrade -r requirements.txt
```

### 4. Мониторинг логов

```bash
# Следите за подозрительной активностью
sudo journalctl -u discordbot -f
```

---

## Обслуживание

### Обновление бота

**Через Git:**
```bash
cd ~/dbot
git pull
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart discordbot
```

**Ручное обновление:**
```bash
# Загрузите новые файлы на сервер
# Перезапустите бота
sudo systemctl restart discordbot
```

### Резервное копирование

```bash
# Создайте backup скрипт
nano ~/backup.sh
```

**Содержимое backup.sh:**
```bash
#!/bin/bash
BACKUP_DIR="/home/discordbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Бэкап config.json и .env
tar -czf $BACKUP_DIR/dbot_backup_$DATE.tar.gz \
  /home/discordbot/dbot/config.json \
  /home/discordbot/dbot/.env

# Удалить старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "dbot_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: dbot_backup_$DATE.tar.gz"
```

**Автоматизируйте через cron:**
```bash
# Сделайте скрипт исполняемым
chmod +x ~/backup.sh

# Добавьте в crontab (ежедневно в 3:00)
crontab -e

# Добавьте строку:
0 3 * * * /home/discordbot/backup.sh
```

### Мониторинг производительности

```bash
# Использование CPU и RAM
htop

# Или
top

# Логи systemd
sudo journalctl -u discordbot --since "1 hour ago"

# Размер логов
du -h /var/log/

# Очистка старых логов
sudo journalctl --vacuum-time=7d
```

---

## Решение проблем

### Бот не запускается

```bash
# Проверьте логи
sudo journalctl -u discordbot -n 50

# Проверьте права
ls -la ~/dbot/.env
ls -la ~/dbot/config.json

# Проверьте Python окружение
source ~/dbot/venv/bin/activate
python --version
pip list
```

### Бот отключается

```bash
# Проверьте, включен ли автозапуск
sudo systemctl is-enabled discordbot

# Проверьте статус
sudo systemctl status discordbot

# Проверьте ошибки в коде
cd ~/dbot
source venv/bin/activate
python bot.py
```

### Нет доступа к интернету

```bash
# Проверьте подключение
ping discord.com

# Проверьте DNS
cat /etc/resolv.conf

# Проверьте файрвол
sudo ufw status
```

---

## Быстрый старт (для опытных)

### Ubuntu one-liner:

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip git && \
git clone https://github.com/ваш_репозиторий/dbot.git && \
cd dbot && python3.11 -m venv venv && source venv/bin/activate && \
pip install -r requirements.txt && \
nano .env && nano config.json && \
sudo tee /etc/systemd/system/discordbot.service > /dev/null <<EOF
[Unit]
Description=Discord Bot
After=network.target
[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin"
ExecStart=$PWD/venv/bin/python $PWD/bot.py
Restart=always
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now discordbot
```

---

## Дополнительные ресурсы

- **Discord Developer Portal:** https://discord.com/developers/applications
- **Python.org:** https://www.python.org/
- **Docker Hub:** https://hub.docker.com/
- **DigitalOcean Tutorials:** https://www.digitalocean.com/community/tutorials

---

## Поддержка

Если возникли проблемы:
1. Проверьте логи: `sudo journalctl -u discordbot -n 100`
2. Убедитесь, что токен правильный
3. Проверьте интернет-соединение
4. Убедитесь, что Python 3.8+
5. Проверьте права на файлы

---

**Готово!** Ваш бот теперь работает 24/7 на выделенном сервере. 🚀
