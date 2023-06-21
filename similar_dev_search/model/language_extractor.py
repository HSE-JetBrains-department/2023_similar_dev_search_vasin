import os
from collections import defaultdict
from typing import Tuple

import enry
import httpx

from model.constants import HEADERS
from model.languages import ALL_LANGUAGES


async def fetch_language_variables(repo_path: str, file_name: str, source_code: bytes = None,
                                   asyncio_client: httpx.AsyncClient = None) -> \
        Tuple[str, defaultdict[int]]:
    """
    Returns language used and dict of variables from file
    :param source_code: source code, if it is already extracted
    :param repo_path: path to the repo
    :param file_name: name of the file
    :param asyncio_client: asyncio client to perform requests from
    :return: language and dict of variables
    """
    if asyncio_client is None:
        client = httpx.AsyncClient(timeout=None)
    else:
        client = asyncio_client
    if source_code is None:
        response = await client.get(repo_path, headers=HEADERS)
        source_code = bytes(response.text, encoding='utf8')

    with open(os.path.join(repo_path, file_name)):
        lang, _ = enry.get_language_by_content(file_name, source_code)
        if lang == '':
            lang, _ = enry.get_language_by_filename(file_name)

        variables = defaultdict(int)

    if lang in ALL_LANGUAGES:
        pass
        # NOT YET SUPPORTED - added in the next pr

    return lang, variables
