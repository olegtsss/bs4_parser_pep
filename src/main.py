import csv
import re
import logging
import os
from urllib.parse import urljoin, urlparse

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL, EXPECTED_STATUS, MISMATCHED_STATUS_MESSAGE
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    # https://docs.python.org/3/whatsnew/
    response = get_response(session, whats_new_url)
    if response is None:
        # Если основная страница не загрузится, программа закончит работу.
        return
    soup = BeautifulSoup(response.text, features='lxml')
    # main_div = soup.find('section', attrs={'id': 'what-s-new-in-python'})
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    # div_with_ul = main_div.find('div', attrs={'class': 'toctree-wrapper'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    # results = []
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        # version_a_tag = section.find('a')
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            # Если не загрузится, программа перейдёт к следующей ссылке.
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        # h1 = soup.find('h1')
        h1 = find_tag(soup, 'h1')
        # dl = soup.find('dl')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    # for row in results:
    #    print(*row)
    return results


def latest_versions(session):
    # https://docs.python.org/3/
    # session = requests_cache.CachedSession()
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    # sidebar = soup.find('div', attrs={'class': 'sphinxsidebarwrapper'})
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')
    # results = []
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        # <a href="https://docs.python.org/3.12/">
        #   Python 3.12 (in development)</a>
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    # for row in results:
    #     print(*row)
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    # https://docs.python.org/3/download.html
    # session = requests_cache.CachedSession()
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    # main_tag = soup.find('div', {'role': 'main'})
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    # table_tag = main_tag.find('table', {'class': 'docutils'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    # pdf_a4_tag = table_tag.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    # https://docs.python.org/3/archives/python-3.11.3-docs-pdf-a4.zip
    filename = os.path.split(urlparse(archive_url).path)[-1]
    # filename = archive_url.split('/')[-1]
    # python-3.11.3-docs-pdf-a4.zip
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    session = requests_cache.CachedSession()
    response = get_response(session, MAIN_PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    numerical_index_section = find_tag(
        soup, 'section', attrs={'id': 'numerical-index'}
    )
    tbody = numerical_index_section.find('tbody')
    peps = tbody.find_all('tr')
    result = [('Статус', 'Количество')]
    peps_result = {}
    for row_pep in peps:
        pep = row_pep.find_all('td')
        # preview_status = first_column_tag.text[1:]
        preview_status = EXPECTED_STATUS.get(pep[0].text[1:2])
        number = pep[1].text
        href = pep[1].find('a')['href']
        title = pep[2].text
        authors = pep[3].text
        pep_url = urljoin(MAIN_PEP_URL, href)
        response = get_response(session, pep_url)
        if response is None:
            return
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
        # peps_result = {
        #     'Active': 31,
        #     'Withdrawn': 56,
        #     'Final': 272,
        #     'Superseded': 20,
        #     'Rejected': 122,
        #     'Deferred': 37,
        #     'April Fool!': 1,
        #     'Accepted': 50,
        #     'Draft': 23
        # }
    return [
        ('Статус', 'Количество'),
        *peps_result.items(),
        ('Total', sum(peps_result.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    # Запускаем функцию с конфигурацией логов.
    configure_logging()
    # Отмечаем в логах момент запуска программы.
    logging.info('Парсер запущен!')

    # Конфигурация парсера аргументов командной строки —
    # передача в функцию допустимых вариантов выбора.
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки.
    args = arg_parser.parse_args()
    # Логируем переданные аргументы командной строки.
    logging.info(f'Аргументы командной строки: {args}')

    # Создание кеширующей сессии.
    session = requests_cache.CachedSession()
    # Если был передан ключ '--clear-cache', то args.clear_cache == True.
    if args.clear_cache:
        # Очистка кеша.
        session.cache.clear()

    # Получение из аргументов командной строки нужного режима работы.
    parser_mode = args.mode
    # Поиск и вызов нужной функции по ключу словаря.
    results = MODE_TO_FUNCTION[parser_mode](session)
    # Если из функции вернулись какие-то результаты,
    if results is not None:
        # передаём их в функцию вывода вместе с аргументами командной строки.
        control_output(results, args)
    # Логируем завершение работы парсера.
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
