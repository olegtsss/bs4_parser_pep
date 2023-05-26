from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException


HTTP_GET_ERROR_MESSAGE = (
    'При загрузке страницы {url} возникла ошибка {error}'
)
FIND_TAG_ERROR_MESSAGE = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as error:
        raise ConnectionError(
            HTTP_GET_ERROR_MESSAGE.format(url=url, error=error),
        )


def find_tag(soup, tag, attrs=None):
    """Перехват ошибки поиска тегов."""
    searched_tag = soup.find(tag, attrs=({} if attrs is None else attrs))
    if not searched_tag:
        raise ParserFindTagException(
            FIND_TAG_ERROR_MESSAGE.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def create_soup(session, url, features='lxml'):
    return BeautifulSoup(
        get_response(session, url).text,
        features=features
    )
