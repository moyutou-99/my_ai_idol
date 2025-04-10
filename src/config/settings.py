import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
CACHE_DIR = DATA_DIR / "cache"

# 创建必要的目录
for directory in [DATA_DIR, MODELS_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Live2D配置
LIVE2D_MODEL_PATH = MODELS_DIR / "live2d"
LIVE2D_MODEL_PATH.mkdir(exist_ok=True)

# 语音配置
VOICE_MODEL_PATH = MODELS_DIR / "voice"
VOICE_MODEL_PATH.mkdir(exist_ok=True)

# LLM配置
LLM_CONFIG = {
    "local": {
        "model": "ollama",
        "model_name": "llama2",
        "api_base": "http://localhost:11434"
    },
    "cloud": {
        "model": "deepseek",
        "api_key": "",  # 需要用户配置
        "api_base": "https://api.deepseek.com/v1"
    }
}

# 数据库配置
DATABASE_CONFIG = {
    "sqlite": {
        "path": DATA_DIR / "database.sqlite"
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0
    }
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    "rotation": "1 day",
    "retention": "7 days"
} 