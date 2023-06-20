import os
from collections import defaultdict
from pathlib import Path
from typing import Tuple

import enry
import git
import httpx
from tree_sitter import Language, Parser

from model.constants import HEADERS
from model.languages import ALL_LANGUAGES


async def fetch_language_variables(file_url: str, file_name: str, source_code: bytes = None,
                                   asyncio_client: httpx.AsyncClient = None) -> \
        Tuple[str, defaultdict[int]]:
    """
    Returns language used and dict of variables from file
    :param source_code: source code, if it is already extracted
    :param file_url: url of file on github
    :param file_name: name of the file
    :param asyncio_client: asyncio client to perform requests from
    :return: language and dict of variables
    """
    if asyncio_client is None:
        client = httpx.AsyncClient(timeout=None)
    else:
        client = asyncio_client
    if source_code is None:
        response = await client.get(file_url, headers=HEADERS)
        source_code = bytes(response.text, encoding='utf8')

    lang, _ = enry.get_language_by_content(file_name, source_code)
    if lang == '':
        lang, _ = enry.get_language_by_filename(file_name)

    variables = defaultdict(int)
    if lang in ALL_LANGUAGES:
        pass
        # NOT YET SUPPORTED - added in the next pr

    if asyncio_client is None:
        await client.aclose()

    return lang, variables
