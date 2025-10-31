import logging
import sys
from app.common.config import LOG_LEVEL

logger = logging.getLogger("ttkt_heroes_out")
logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.DEBUG))
if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.DEBUG))
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
    ch.setFormatter(fmt)
    logger.addHandler(ch)
