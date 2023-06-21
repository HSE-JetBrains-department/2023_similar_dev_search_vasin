import os
from collections import Counter
from pathlib import Path
from typing import Tuple

import enry
import git
import httpx
from dulwich.repo import Repo
from tree_sitter import Language, Parser

from model.constants import HEADERS
from model.languages import ALL_LANGUAGES


def fetch_treesitter_repo(url: str) -> Repo:
    """
    clones a repository with treesitter language specification
    :param url: url of the repo
    :return: dulwich Repo for a language
    """
    repo_name = url[url.rfind('/') + 1:]
    path_to_repo = str(Path(f"{Path().cwd().parent}/treesitter/{repo_name}"))
    parent_path = str(Path(path_to_repo).parent)

    if not os.path.exists(parent_path):
        os.makedirs(parent_path)
    if os.path.exists(path_to_repo):
        return Repo(path_to_repo)
    print('cloning', url)
    git.Repo.clone_from(url, path_to_repo)
    return Repo(path_to_repo)


supported_languages = ['c', 'c-sharp', 'cpp']  # , 'kotlin', 'python', 'javascript', 'java']
aliases = {'c#': 'c-sharp', 'c++': 'cpp', 'js': 'javascript'}
TREE_SITTER_C_SHARP = fetch_treesitter_repo("https://github.com/tree-sitter/tree-sitter-c-sharp")
TREE_SITTER_C = fetch_treesitter_repo("https://github.com/tree-sitter/tree-sitter-c")
TREE_SITTER_CPP = fetch_treesitter_repo("https://github.com/tree-sitter/tree-sitter-cpp")
TREE_SITTER_KOTLIN = fetch_treesitter_repo("https://github.com/fwcd/tree-sitter-kotlin")
TREE_SITTER_PYTHON = fetch_treesitter_repo("https://github.com/tree-sitter/tree-sitter-python")
TREE_SITTER_JAVASCRIPT = fetch_treesitter_repo("https://github.com/tree-sitter/tree-sitter-javascript")
TREE_SITTER_JAVA = fetch_treesitter_repo("https://github.com/tree-sitter/tree-sitter-java")

path_to_build = str(Path(f"{Path.cwd().parent}/build/my-languages.so"))
Language.build_library(
    path_to_build,
    [
        str(Path(TREE_SITTER_C_SHARP.path)),
        str(Path(TREE_SITTER_C.path)),
        str(Path(TREE_SITTER_CPP.path)),
        str(Path(TREE_SITTER_KOTLIN.path)),
        str(Path(TREE_SITTER_PYTHON.path)),
        str(Path(TREE_SITTER_JAVASCRIPT.path)),
        str(Path(TREE_SITTER_JAVA.path))
    ]
)


def get_variables(language: str, code: bytes) -> Counter[int]:
    """
    Returns variables from code
    :param language: language of the code
    :param code: source code
    :return: dict of variables {variable_name: occurrences}
    """
    identifiers = Counter(int)
    parser = Parser()
    language = language.lower()

    if language in aliases:
        language = aliases[language]

    if language not in supported_languages:
        return identifiers

    file_lang = Language(f"{Path().cwd().parent}/build/my-languages.so", language)
    parser.set_language(file_lang)

    query = file_lang.query("(identifier) @variable")
    captures = query.captures(parser.parse(code).root_node)
    for capture in captures:
        node = capture[0]
        identifier = code[node.start_byte: node.end_byte].decode()
        identifiers[identifier] += 1
    return identifiers


async def fetch_language_variables(file_url: str, file_name: str, source_code: bytes = None,
                                   asyncio_client: httpx.AsyncClient = None) -> \
        Tuple[str, Counter[int]]:
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

    variables = Counter(int)
    if lang in ALL_LANGUAGES:
        variables = get_variables(lang, source_code)

    if asyncio_client is None:
        await client.aclose()

    return lang, variables
