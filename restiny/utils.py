import shlex
from collections.abc import Iterable
from pathlib import Path
from typing import Union

import httpx


def build_curl_cmd(
    method: str,
    url: str,
    headers: Union[dict[str, str], None] = None,
    params: Union[dict[str, str], None] = None,
    body_raw: Union[str, None] = None,
    body_form_urlencoded: Union[dict[str, str], None] = None,
    body_form_multipart: Union[dict[str, str, Path], None] = None,
    body_files: Union[list[Path], None] = None,
    auth_basic: Union[tuple[str, str], None] = None,
    auth_bearer: Union[str, None] = None,
    auth_api_key_header: Union[tuple[str, str], None] = None,
    auth_api_key_param: Union[tuple[str, str], None] = None,
    auth_digest: Union[tuple[str, str], None] = None,
) -> str:
    cmd_parts = ['curl']

    # Method
    cmd_parts.extend(['--request', method])

    # URL + Params
    if params:
        url = str(httpx.URL(url).copy_merge_params(params))
    cmd_parts.extend(['--url', shlex.quote(url)])

    # Headers
    for header_key, header_value in headers.items():
        header = f'{header_key}: {header_value}'
        cmd_parts.extend(['--header', shlex.quote(header)])

    # Body
    if body_raw:
        cmd_parts.extend(['--data', shlex.quote(body_raw)])
    elif body_form_urlencoded:
        for form_key, form_value in body_form_urlencoded.items():
            cmd_parts.extend(
                ['--data', shlex.quote(f'{form_key}={form_value}')]
            )
    elif body_form_multipart:
        for form_key, form_value in body_form_multipart.items():
            if isinstance(form_value, str):
                cmd_parts.extend(
                    ['--form', shlex.quote(f'{form_key}={form_value}')]
                )
            if isinstance(form_value, Path):
                cmd_parts.extend(
                    ['--form', shlex.quote(f'{form_key}=@{form_value}')]
                )
    elif body_files:
        for file in body_files:
            cmd_parts.extend(['--data', shlex.quote(f'@{file}')])

    # Auth
    if auth_basic:
        user, pwd = auth_basic
        cmd_parts.extend(['--user', shlex.quote(f'{user}:{pwd}')])
    elif auth_bearer:
        token = auth_bearer
        cmd_parts.extend(['--header', shlex.quote(f'Authorization: {token}')])
    elif auth_api_key_header:
        key, value = auth_api_key_header
        cmd_parts.extend(['--header', shlex.quote(f'{key}: {value}')])
    elif auth_api_key_param:
        key, value = auth_api_key_param
        url_arg_index = cmd_parts.index('--url')
        new_url = str(httpx.URL(url).copy_merge_params({key: value}))
        cmd_parts[url_arg_index + 1] = shlex.quote(new_url)
    elif auth_digest:
        user, pwd = auth_digest
        cmd_parts.extend(['--digest', '--user', shlex.quote(f'{user}:{pwd}')])

    return ' '.join(cmd_parts)


def filter_paths(
    paths: Iterable[Path],
    show_hidden_dirs: bool = False,
    show_hidden_files: bool = False,
    allowed_file_suffixes: Union[list[str], None] = None,
) -> list[Path]:
    """
    Filters a list of paths, hiding or showing hidden directories and files.
    """
    filtered_paths = []
    for path in paths:
        if path.is_dir():
            if not show_hidden_dirs and str(path.name).startswith('.'):
                continue
            filtered_paths.append(path)
        elif path.is_file():
            if not show_hidden_files and str(path.name).startswith('.'):
                continue
            if (
                allowed_file_suffixes is not None
                and path.suffix not in allowed_file_suffixes
            ):
                continue
            filtered_paths.append(path)
    return filtered_paths


def is_multiple_of(number: int, multiple_of: int) -> bool:
    """
    Checks if a number is a multiple of another.
    """
    return number % multiple_of == 0


def next_multiple_of(current_number: int, multiple_of: int) -> int:
    """
    Returns the next multiple of a base number from a current number.
    """
    return ((current_number // multiple_of) + 1) * multiple_of


def previous_multiple_of(current_number: int, multiple_of: int) -> int:
    """
    Returns the previous multiple of a base number before a current number.
    """
    return ((current_number - 1) // multiple_of) * multiple_of


def first_char_non_empty(text: str) -> Union[int, None]:
    """
    Returns the index of the first non-empty character in a string.
    """
    for index, char in enumerate(text):
        if char != ' ':
            return index


def seconds_to_milliseconds(seconds: Union[int, float]) -> int:
    return round(seconds * 1000)


def shorten_string(value: str, max_lenght: int, elipsis: str = '..') -> str:
    if len(value) <= max_lenght:
        return value

    return value[: max_lenght - len(elipsis)] + elipsis
