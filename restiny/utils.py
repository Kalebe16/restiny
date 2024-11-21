import shlex
from collections.abc import Iterable
from pathlib import Path

import httpx


def build_curl_cmd(
    method: str,
    url: str,
    headers: dict[str, str] = {},
    params: dict[str, str] = {},
    raw_body: str | None = None,
    form_urlencoded: dict[str, str] = {},
    form_multipart: dict[str, str | Path] = {},
    files: list[Path] = [],
) -> str:
    cmd_parts = ['curl']
    cmd_parts.extend(['--request', method])

    url = str(httpx.URL(url).copy_merge_params(params))
    cmd_parts.extend(['--url', shlex.quote(url)])

    for header_key, header_value in headers.items():
        header = f'{header_key}: {header_value}'
        cmd_parts.extend(['--header', shlex.quote(header)])

    if raw_body:
        cmd_parts.extend(['--data', shlex.quote(raw_body)])
    elif form_urlencoded:
        for form_key, form_value in form_urlencoded.items():
            cmd_parts.extend(
                ['--data', shlex.quote(f'{form_key}={form_value}')]
            )
    elif form_multipart:
        for form_key, form_value in form_multipart.items():
            if isinstance(form_value, str):
                cmd_parts.extend(
                    ['--form', shlex.quote(f'{form_key}={form_value}')]
                )
            if isinstance(form_value, Path):
                cmd_parts.extend(
                    ['--form', shlex.quote(f'{form_key}=@{form_value}')]
                )
    elif files:
        for file in files:
            cmd_parts.extend(['--data', shlex.quote(f'@{file}')])

    return ' '.join(cmd_parts)


def filter_paths(
    paths: Iterable[Path],
    show_hidden_dirs: bool = False,
    show_hidden_files: bool = False,
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


def first_char_non_empty(text: str) -> int | None:
    """
    Returns the index of the first non-empty character in a string.
    """
    for index, char in enumerate(text):
        if char != ' ':
            return index


def seconds_to_milliseconds(seconds: int | float) -> int:
    return round(seconds * 1000)
