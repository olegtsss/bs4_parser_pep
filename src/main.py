import logging
import os
import re
from urllib.parse import urljoin, urlparse

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, DOWNLOAD_DIR, DOWNLOAD_MESSAGE,
                       EXPECTED_STATUS, LATEST_VERSIONS_HEAD,
                       LATEST_VERSIONS_MESSAGE, MAIN_DOC_URL, MAIN_PEP_URL,
                       MISMATCHED_STATUS_MESSAGE, PARSER_ARGS_MESSAGE,
                       PARSER_START_MESSAGE, PARSER_STOP_MESSAGE, PEPS_HEAD,
                       PEPS_TAIL, WHATS_NEW_HEAD)
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    """
    Запуск парсера информации из статей о нововведениях в Python.
    https://docs.python.org/3/whatsnew/
    """
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = []
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            # Если не загрузится, программа перейдёт к следующей ссылке
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return [WHATS_NEW_HEAD, *results]


def latest_versions(session):
    """
    Запуск парсера статусов версий Python.
    https://docs.python.org/3/
    """
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception(LATEST_VERSIONS_MESSAGE)
    results = []
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    return [LATEST_VERSIONS_HEAD, *results]


def download(session):
    """
    Запуск парсера, который скачивает архив документации Python.
    https://docs.python.org/3/download.html
    """
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
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
    response = get_response(session, MAIN_PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    numerical_index_section = find_tag(
        soup, 'section', attrs={'id': 'numerical-index'}
    )
    tbody = numerical_index_section.find('tbody')
    peps = tbody.find_all('tr')
    peps_result = {}
    for row_pep in peps:
        pep = row_pep.find_all('td')
        preview_status = EXPECTED_STATUS.get(pep[0].text[1:2])
        number = pep[1].text
        href = pep[1].find('a')['href']
        title = pep[2].text
        authors = pep[3].text
        pep_url = urljoin(MAIN_PEP_URL, href)
        response = get_response(session, pep_url)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        dl = find_tag(soup, 'dl')
        status = dl.find(string='Status').parent.find_next_sibling().text
        if preview_status is None or status not in preview_status:
            print(
                MISMATCHED_STATUS_MESSAGE.format(
                    pep_url=pep_url, status=status,
                    preview_status=preview_status)
            )
        if status not in peps_result:
            peps_result[status] = 1
        else:
            peps_result[status] += 1
        logging.info(
            f'{number}, {preview_status}, {title}, {authors}, {pep_url}')
    return [
        PEPS_HEAD, *peps_result.items(), (PEPS_TAIL, sum(peps_result.values()))
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
    args = arg_parser.parse_args()
    logging.info(PARSER_ARGS_MESSAGE.format(args=args))
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info(PARSER_STOP_MESSAGE)


if __name__ == '__main__':
    main()
