import argparse
import logging
from logging.handlers import RotatingFileHandler

from constants import BASE_DIR, DT_FORMAT, LOG_DIR, LOG_FILENAME, LOG_FORMAT


def configure_argument_parser(available_modes):
    """Парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=('pretty', 'file'),
        help='Дополнительные способы вывода данных'
    )
    return parser


def configure_logging():
    """Логгер с выводом сообщений в терминал."""
    log_dir = BASE_DIR / LOG_DIR
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / LOG_FILENAME
    rotating_handler = RotatingFileHandler(
        log_file, maxBytes=10 ** 6, backupCount=5, encoding='utf-8'
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        # Вывод логов в терминал
        handlers=(rotating_handler, logging.StreamHandler())
    )
