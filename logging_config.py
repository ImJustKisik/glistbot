import logging
import logging.config
import json
from pathlib import Path

def setup_logging(default_path='logging_config.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """Настройка конфигурации логирования"""
    path = default_path
    value = Path(path)
    if value.exists():
        with open(value, 'rt') as f:
            try:
                config = json.load(f)
                logging.config.dictConfig(config)
            except json.JSONDecodeError as e:
                logging.basicConfig(level=default_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                logging.warning(f"Ошибка чтения файла конфигурации логирования: {e}. Используется базовая конфигурация.")
    else:
        logging.basicConfig(level=default_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.info("Файл конфигурации логирования не найден. Используется базовая конфигурация.")
