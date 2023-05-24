from pathlib import Path


LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_DIR = 'logs'
LOG_FILENAME = 'parser.log'
MAIN_DOC_URL = 'https://docs.python.org/3/'
MAIN_PEP_URL = 'https://peps.python.org/'
BASE_DIR = Path(__file__).parent
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
MISMATCHED_STATUS_MESSAGE = (
    'Несовпадающие статусы:\n'
    '{pep_url}\n'
    'Статус в карточке: {status}\n'
    'Ожидаемые статусы: {preview_status}'
)
PEPS_DIR = 'results'
PEPS_HEAD = ('Статус', 'Количество')
PEPS_TAIL = 'Total'
DOWNLOAD_DIR = 'downloads'
FILE_SAVE_MESSAGE = 'Файл с результатами был сохранён: {file_path}'
DOWNLOAD_MESSAGE = 'Архив был загружен и сохранён: {archive_path}'
HTTP_GET_ERROR_MESSAGE = 'Возникла ошибка при загрузке страницы {url}'
FIND_TAG_ERROR_MESSAGE = 'Не найден тег {tag} {attrs}'
WHATS_NEW_HEAD = ('Ссылка на статью', 'Заголовок', 'Редактор, Автор')
LATEST_VERSIONS_MESSAGE = 'Ничего не нашлось'
LATEST_VERSIONS_HEAD = ('Ссылка на документацию', 'Версия', 'Статус')
PARSER_START_MESSAGE = 'Парсер запущен!'
PARSER_ARGS_MESSAGE = 'Аргументы командной строки: {args}'
PARSER_STOP_MESSAGE = 'Парсер завершил работу.'
