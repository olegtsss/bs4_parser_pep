import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (BASE_DIR, DATETIME_FORMAT, DEFAULT_OUTPUT, FILE_OUTPUT,
                       PEPS_DIR, PRETTY_OUTPUT)


FILE_SAVE_MESSAGE = 'Файл с результатами был сохранён: {file_path}'


def default_output(results, *args):
    """Вывод данных в терминал построчно."""
    for row in results:
        print(*row)


def pretty_output(results, *args):
    """Вывод данных в формате PrettyTable."""
    table = PrettyTable()
    table.field_names = results[0]
    # Выравниваем всю таблицу по левому краю
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    """Создание директории с результатами парсинга."""
    results_dir = BASE_DIR / PEPS_DIR
    results_dir.mkdir(exist_ok=True)
    # Получаем режим работы парсера из аргументов командной строки
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    # 2021-06-18_07-40-41
    file_path = results_dir / f'{parser_mode}_{now_formatted}.csv'
    with open(file_path, 'w', encoding='utf-8') as file:
        csv.writer(file, csv.unix_dialect).writerows(results)
    logging.info(FILE_SAVE_MESSAGE.format(file_path=file_path))


OUTPUT_FORMAT = {
    PRETTY_OUTPUT: pretty_output,
    FILE_OUTPUT: file_output,
    DEFAULT_OUTPUT: default_output
}


def control_output(results, cli_args):
    """Контроль вывода результатов парсинга."""
    OUTPUT_FORMAT.get(cli_args.output)(results, cli_args)
