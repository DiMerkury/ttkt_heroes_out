# common/logger.py
import logging
import sys

# --- Настройка форматирования ---
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"

# --- Конфигурация логгера ---
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    stream=sys.stdout,
)

# --- Основной логгер проекта ---
logger = logging.getLogger("dungeon")

# --- Уровни для разных подсистем (опционально) ---
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
