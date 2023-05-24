import logging

from requests import RequestException

from constants import FIND_TAG_ERROR_MESSAGE, HTTP_GET_ERROR_MESSAGE
from exceptions import ParserFindTagException


def get_response(session, url):
    """Перехват ошибки RequestException."""
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            HTTP_GET_ERROR_MESSAGE.format(url=url),
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    """Перехват ошибки поиска тегов."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = FIND_TAG_ERROR_MESSAGE.format(tag=tag, attrs=attrs)
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag
