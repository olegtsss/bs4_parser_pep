import logging
import os
import re
from collections import defaultdict
from urllib.parse import urljoin, urlparse

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, DOWNLOAD_DIR, EXPECTED_STATUS, MAIN_DOC_URL,
                       MAIN_PEP_URL)
from exceptions import ParserFindTagException
from outputs import control_output
from utils import create_soup, find_tag


LATEST_VERSIONS_MESSAGE = 'Ничего не нашлось'
PARSER_START_MESSAGE = 'Парсер запущен!'
PARSER_ARGS_MESSAGE = 'Аргументы командной строки: {args}'
PARSER_STOP_MESSAGE = 'Парсер завершил работу.'
ERROR_MESSAGE = 'Ошибка: {error}'
DOWNLOAD_MESSAGE = 'Архив был загружен и сохранён: {archive_path}'
RESPONSE_IS_NONE = 'Страница не загружена: {url}'
MISMATCHED_STATUS_MESSAGE = (
    'Несовпадающие статусы:\n'
    '{pep_url}\n'
    'Статус в карточке: {status}\n'
    'Ожидаемые статусы: {preview_status}'
)
PEPS_HEAD = ('Статус', 'Количество')
PEPS_TAIL = 'Всего'
WHATS_NEW_HEAD = ('Ссылка на статью', 'Заголовок', 'Редактор, Автор')
LATEST_VERSIONS_HEAD = ('Ссылка на документацию', 'Версия', 'Статус')


def whats_new(session):
    """
    Запуск парсера информации из статей о нововведениях в Python.
    https://docs.python.org/3/whatsnew/
    """
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = create_soup(session, whats_new_url)
    sections_by_python = soup.select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1 a')
    results = []
    logs = []
    for section in tqdm(sections_by_python):
        version_link = urljoin(whats_new_url, section['href'])
        try:
            soup = create_soup(session, version_link)
            results.append(
                (
                    version_link,
                    find_tag(soup, 'h1').text,
                    find_tag(soup, 'dl').text.replace('\n', ' ')
                )
            )
        except ConnectionError:
            # Если не загрузится, программа перейдёт к следующей ссылке
            logs.append(RESPONSE_IS_NONE.format(url=version_link))
            continue
    list(map(logging.info, logs))
    return [WHATS_NEW_HEAD, *results]


def latest_versions(session):
    """
    Запуск парсера статусов версий Python.
    https://docs.python.org/3/
    """
    soup = create_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise ParserFindTagException(LATEST_VERSIONS_MESSAGE)
    results = []
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((a_tag['href'], version, status))
    return [LATEST_VERSIONS_HEAD, *results]


def download(session):
    """
    Запуск парсера, который скачивает архив документации Python.
    https://docs.python.org/3/download.html
    """
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = create_soup(session, downloads_url)
    pdf_a4_link = soup.select_one(
        'table.docutils td > a[href$="pdf-a4.zip"]')['href']
    if pdf_a4_link is None:
        raise ParserFindTagException(LATEST_VERSIONS_MESSAGE)
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = os.path.split(urlparse(archive_url).path)[-1]
    downloads_dir = BASE_DIR / DOWNLOAD_DIR
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_MESSAGE.format(archive_path=archive_path))


def pep(session):
    """
    Запуск парсера и получение статистики по PEP.
    https://peps.python.org/
    """
    soup = create_soup(session, MAIN_PEP_URL)
    numerical_index_section = find_tag(
        soup, 'section', attrs={'id': 'numerical-index'}
    )
    tbody = numerical_index_section.find('tbody')
    peps = tbody.find_all('tr')
    peps_result = defaultdict(int)
    logs = []
    for row_pep in tqdm(peps):
        pep = row_pep.find_all('td')
        preview_status = EXPECTED_STATUS.get(pep[0].text[1:2])
        number = pep[1].text
        href = pep[1].find('a')['href']
        title = pep[2].text
        authors = pep[3].text
        pep_url = urljoin(MAIN_PEP_URL, href)
        try:
            soup = create_soup(session, pep_url)
            dl = find_tag(soup, 'dl')
            status = dl.find(string='Status').parent.find_next_sibling().text
            if preview_status is None or status not in preview_status:
                logs.append(
                    MISMATCHED_STATUS_MESSAGE.format(
                        pep_url=pep_url, status=status,
                        preview_status=preview_status)
                )
            peps_result[status] += 1
            logs.append(
                f'{number}, {preview_status}, {title}, {authors}, {pep_url}')
        except ConnectionError:
            # Если не загрузится, программа перейдёт к следующей ссылке
            logs.append(RESPONSE_IS_NONE.format(url=pep_url))
            continue
    list(map(logging.info, logs))
    return [
        PEPS_HEAD,
        *peps_result.items(),
        (PEPS_TAIL, sum(peps_result.values()))
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    """Точка входа парсера."""
    configure_logging()
    logging.info(PARSER_START_MESSAGE)
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки
    try:
        args = arg_parser.parse_args()
        logging.info(PARSER_ARGS_MESSAGE.format(args=args))
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as error:
        logging.exception(ERROR_MESSAGE.format(error=error))
    logging.info(PARSER_STOP_MESSAGE)


if __name__ == '__main__':
    main()
