import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file="linkedin.log", level=logging.INFO):
    """"
      Logger setup function
      Args:
        name: logger name
        log_file: log file name
        level: logging level
    Returns:
        logger object
    """
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=1)

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger