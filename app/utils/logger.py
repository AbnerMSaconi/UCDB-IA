# app/utils/logger.py
import logging
from loguru import logger
import sys

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe().f_back, 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
     
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | {message}",
        level="DEBUG"  # <-- ALTERAÇÃO IMPORTANTE AQUI
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0)