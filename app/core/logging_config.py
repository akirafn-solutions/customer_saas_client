import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_loggers_cache = {}


def setup_logging(logger_name: str, log_file: str = None) -> logging.Logger:
    if logger_name in _loggers_cache:
        return _loggers_cache[logger_name]
    
    try:
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"⚠️  Aviso: Não foi possível criar diretório de logs: {e}")
                log_file = None
        
        # 2. Formato do Log
        log_formatter = logging.Formatter(
            '%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Limpar handlers anteriores para evitar duplicação
        logger.handlers.clear()
        
        if log_file:
            try:
                file_handler = RotatingFileHandler(
                    log_file,
                    mode='a',
                    maxBytes=5*1024*1024,  # 5MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setFormatter(log_formatter)
                logger.addHandler(file_handler)
                print(f"✅ Logger configurado com arquivo: {log_file}")
            except Exception as e:
                print(f"⚠️  Aviso: Não foi possível configurar arquivo de log: {e}")

        # 5. Handler para console (stdout)
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível configurar console handler: {e}")

        def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            try:
                logger.critical(
                    "Exceção não tratada capturada pelo hook global:",
                    exc_info=(exc_type, exc_value, exc_traceback)
                )
            except Exception:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)

        sys.excepthook = handle_uncaught_exception
        
        _loggers_cache[logger_name] = logger
        
        return logger
        
    except Exception as e:
        print(f"❌ Erro crítico ao configurar logger: {e}")
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(console_handler)
        _loggers_cache[logger_name] = logger
        return logger


def get_logger(logger_name: str) -> logging.Logger:
    if logger_name in _loggers_cache:
        return _loggers_cache[logger_name]
    return logging.getLogger(logger_name)