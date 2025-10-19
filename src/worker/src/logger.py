import logging
from common.utils import is_valid_destination_file_path

def get_logger(func_name: str, log_file_path: str, std_enabled: bool) -> logging.Logger:
    """Inicjalizuje logger.
    
    Args:
        func_name (str): Nazwa funkcji.
        log_file_path (str): Ścieżka do pliku logowania.
        std_enabled (bool): Czy wypisywać logi na stdout.
    
    Returns:
        logging.Logger: Logger.
    """


    if not is_valid_destination_file_path(log_file_path):
        raise ValueError(f"Invalid log file path: {log_file_path}")
    
    logger = logging.getLogger(func_name)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    

    # File handler 
    file_handler = logging.FileHandler(log_file_path, mode='a')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # std handler
    if std_enabled:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

def flush_logger(logger: logging.Logger) -> None:
    """Wymusza zapis wszystkich buforowanych logów do pliku.
    
    Wywołuje metodę flush() na wszystkich handlerach loggera, co powoduje
    natychmiastowe zapisanie buforowanych danych do pliku.
    
    Args:
        logger (logging.Logger): Logger, którego handlery mają być opróżnione.
    """
    for handler in logger.handlers:
        handler.flush()