import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, FILE_SAVE_MESSAGE, PEPS_DIR


def control_output(results, cli_args):
    """Контроль вывода результатов парсинга."""
    output = cli_args.output
    if output == 'pretty':
        pretty_output(results)
    elif output == 'file':
        file_output(results, cli_args)
    else:
        default_output(results)


def default_output(results):
    """Вывод данных в терминал построчно."""
    for row in results:
        print(*row)


def pretty_output(results):
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
        writer = csv.writer(file, dialect='unix')
        writer.writerows(results)
    logging.info(FILE_SAVE_MESSAGE.format(file_path=file_path))
