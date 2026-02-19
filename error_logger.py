"""
Error Logger - Logs errors to a file for debugging
"""
import os
import sys
import logging
from datetime import datetime
from config import APP_NAME

def get_log_path() -> str:
    """Get path to log file in user's AppData"""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    log_dir = os.path.join(appdata, APP_NAME)
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'error.log')


def setup_logging():
    """Set up logging to file and console"""
    log_path = get_log_path()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (for errors)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    
    # Console handler (for info)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_exception(exc_type, exc_value, exc_traceback):
    """Custom exception handler that logs unhandled exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error(
        "Unhandled exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def install_exception_handler():
    """Install the custom exception handler"""
    sys.excepthook = log_exception


# Initialize on import
logger = setup_logging()
install_exception_handler()
