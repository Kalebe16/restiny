from pathlib import Path
from typing import Iterable


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
