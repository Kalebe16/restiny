import ctypes
import os
import platform
import shlex
import shutil
import subprocess
from pathlib import Path

import httpx
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QListView,
    QMainWindow,
    QPushButton,
)


def has_root_privileges() -> bool:
    system = platform.system()
    if system in ('Linux', 'Darwin'):
        return os.geteuid() == 0
    elif system == 'Windows':
        return ctypes.windll.shell32.IsUserAnAdmin()
    return False


def fix_pyside_stylesheet(window: QMainWindow, accent_color: str) -> None:
    for combo in window.findChildren(QComboBox):
        view = QListView(combo)
        combo.setView(view)
    for button in window.findChildren(QPushButton):
        button.setStyleSheet(
            f'QPushButton:focus {{ border: 2px solid {accent_color} }}'
        )
    for checkbox in window.findChildren(QCheckBox):
        checkbox.setStyleSheet(
            f"""\
            QCheckBox:focus {{ border-bottom: 2px solid {accent_color} }}\
            QCheckBox::indicator {{ width: 24px; height: 24px; }}
            """
        )


def open_linux_terminal(command: str) -> None:
    terminals = [
        ('gnome-terminal', ['--', 'bash', '-c']),
        ('ptyxis', ['--', 'bash', '-c']),
        ('kgx', ['--', 'bash', '-c']),
        ('konsole', ['-e', 'bash', '-c']),
        ('xfce4-terminal', ['-e', 'bash', '-c']),
        ('mate-terminal', ['-e', 'bash', '-c']),
        ('lxterminal', ['-e', 'bash', '-c']),
        ('tilix', ['-e', 'bash', '-c']),
        ('terminator', ['-x', 'bash', '-c']),
        ('alacritty', ['-e', 'bash', '-c']),
        ('kitty', ['bash', '-c']),
        ('wezterm', ['start', '--', 'bash', '-c']),
        ('xterm', ['-e', 'bash', '-c']),
        ('x-terminal-emulator', ['-e', 'bash', '-c']),
    ]
    for terminal, args in terminals:
        if shutil.which(terminal):
            subprocess.Popen([terminal, *args, f'{command}; exec bash'])
            return


def open_darwin_terminal(command: str) -> None:
    subprocess.Popen(
        [
            'open',
            '-a',
            'Terminal',
            command,
        ]
    )


def build_curl_cmd(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    body_raw: str | None = None,
    body_form_urlencoded: dict[str, str] | None = None,
    body_form_multipart: dict[str, str | Path] | None = None,
    body_files: list[Path] | None = None,
    auth_basic: tuple[str, str] | None = None,
    auth_bearer: str | None = None,
    auth_api_key_header: tuple[str, str] | None = None,
    auth_api_key_param: tuple[str, str] | None = None,
    auth_digest: tuple[str, str] | None = None,
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
