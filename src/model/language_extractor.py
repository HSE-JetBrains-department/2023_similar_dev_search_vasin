import os
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

import enry
import git
import httpx
from dulwich.repo import Repo
from tree_sitter import Language, Parser

from model.constants import headers
from model.languages import all_languages


def fetch_treesitter_repo(url: str):
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


supported_languages = ['c', 'c-sharp', 'cpp']#, 'kotlin', 'python', 'javascript', 'java']
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


def get_variables(language: str, code: str) -> defaultdict[int]:
    identifiers = defaultdict(int)
    code = bytes(code, 'utf-8')
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


async def fetch_language_variables(file_url: str, file_name: str, asyncio_client: httpx.AsyncClient = None) -> \
        Tuple[str, defaultdict[int]]:
    if asyncio_client is None:
        client = httpx.AsyncClient(timeout=None)
    else:
        client = asyncio_client

    response = await client.get(file_url, headers=headers)
    source_code = response.text

    lang, _ = enry.get_language_by_content(file_name, bytes(source_code, encoding='utf8'))
    if lang == '':
        lang, _ = enry.get_language_by_filename(file_name)

    variables = defaultdict(int)
    if lang in all_languages:
        variables = get_variables(lang, source_code)

    if asyncio_client is None:
        await client.aclose()

    return lang, variables
