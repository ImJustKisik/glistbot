import json
import os
from threading import Lock

class ConfigManager:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, file_path='config.json'):
        if not hasattr(self, 'initialized'):
            self.file_path = file_path
            self.config = {}
            self.lock = Lock()
            self.load_config()
            self.initialized = True

    def load_config(self):
        with self.lock:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"Файл '{self.file_path}' не найден!")
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_all(self):
        return self.config.copy()

    def update_config(self, key, value):
        with self.lock:
            self.config[key] = value
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)

# Создаем единственный экземпляр, который будет использоваться во всем приложении
config_manager = ConfigManager()
