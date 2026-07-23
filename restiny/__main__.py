import asyncio
import os
import platform
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import qasync
from PySide6.QtWidgets import QApplication

from restiny.data.db import DBManager
from restiny.data.repos import (
    EnvironmentsSQLRepo,
    FoldersSQLRepo,
    RequestsSQLRepo,
    SettingsSQLRepo,
)
from restiny.themes import dark, light
from restiny.ui.app import MainWindow
from restiny.utils import (
    fix_pyside_stylesheet,
    is_root,
)


def get_real_python():
    if not getattr(sys, 'frozen', False):
        return sys.executable

    for candidate in ['python3', 'python', 'py']:
        if shutil.which(candidate):
            return candidate

    return sys.executable


def monkey_patch() -> None:
    _real_popen = subprocess.Popen

    def patched_popen(*args, **kwargs):
        cmd = args[0]

        frozen = getattr(sys, 'frozen', False)

        if isinstance(cmd, (list, tuple)) and cmd:
            if frozen and cmd[0] == sys.executable:
                cmd = list(cmd)
                cmd[0] = get_real_python()
                args = (cmd,) + args[1:]

        elif isinstance(cmd, str):
            if frozen and cmd.startswith(sys.executable):
                cmd = cmd.replace(sys.executable, get_real_python(), 1)
                args = (cmd,) + args[1:]

        return _real_popen(*args, **kwargs)

    subprocess.Popen = patched_popen


def run_commands_modal(parent: tk.Tk, commands: list[str]):
    def run_commands_in_thread(log: ScrolledText, commands: list[str]):
        log.tag_config(
            'command', foreground='blue', font=('TkDefaultFont', 10, 'bold')
        )
        log.tag_config('stdout', foreground='green')
        log.tag_config(
            'stderr', foreground='red', font=('TkDefaultFont', 10, 'italic')
        )
        log.tag_config('finished', foreground='gray')

        for cmd in commands:
            log.insert('end', f'>>> {cmd}\n', 'command')
            log.see('end')

            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            for line in process.stdout:
                log.insert('end', line, 'stdout')
                log.see('end')

            for line in process.stderr:
                log.insert('end', line, 'stderr')
                log.see('end')

            process.wait()

        log.insert('end', '[All commands finished]\n', 'finished')
        log.see('end')

    modal = tk.Toplevel(parent)
    modal.title('Installing requirements')
    modal.geometry('700x400')

    log = ScrolledText(modal, height=20, width=80)
    log.pack(expand=True, fill='both', padx=10, pady=10)

    thread = threading.Thread(
        target=lambda: run_commands_in_thread(log=log, commands=commands)
    )
    thread.start()


def show_requirements_popup() -> None:
    def install_requirements(root: tk.Tk) -> None:
        system = platform.system()
        if system == 'Linux':
            if not is_root():
                messagebox.showwarning(
                    'Permissions required',
                    'To install requirements, please run this program with root/administrator privileges.',
                    parent=root,
                )
                return

            if shutil.which('apt'):
                commands = [
                    'DEBIAN_FRONTEND=noninteractive apt install -y libxcb1',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libxcb-cursor0',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libxcb-xinerama0',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libxkbcommon-x11-0',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libgl1',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libegl1',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libnss3',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libasound2t64',
                    'DEBIAN_FRONTEND=noninteractive apt install -y libasound2',
                ]
            elif shutil.which('dnf'):
                commands = [
                    'dnf install -y libxcb',
                    'dnf install -y xcb-util-cursor',
                    'dnf install -y libxkbcommon-x11',
                    'dnf install -y mesa-libGL',
                    'dnf install -y mesa-libEGL',
                    'dnf install -y nss',
                    'dnf install -y alsa-lib',
                ]
            elif shutil.which('yum'):
                commands = [
                    'yum install -y libxcb',
                    'yum install -y xcb-util-cursor',
                    'yum install -y libxkbcommon-x11',
                    'yum install -y mesa-libGL',
                    'yum install -y mesa-libEGL',
                    'yum install -y nss',
                    'yum install -y alsa-lib',
                ]
            elif shutil.which('pacman'):
                commands = [
                    'pacman -Syu --needed --noconfirm libxcb',
                    'pacman -S --needed --noconfirm xcb-util-cursor',
                    'pacman -S --needed --noconfirm libxkbcommon-x11',
                    'pacman -S --needed --noconfirm mesa',
                    'pacman -S --needed --noconfirm nss',
                    'pacman -S --needed --noconfirm alsa-lib',
                ]
            elif shutil.which('zypper'):
                commands = [
                    'zypper --non-interactive install -y libxcb1',
                    'zypper --non-interactive install -y libxcb-cursor0',
                    'zypper --non-interactive install -y libxkbcommon-x11-0',
                    'zypper --non-interactive install -y Mesa-libGL1',
                    'zypper --non-interactive install -y Mesa-libEGL1',
                    'zypper --non-interactive install -y mozilla-nss',
                    'zypper --non-interactive install -y alsa',
                ]
            else:
                messagebox.showerror(
                    'Unsupported distribution',
                    (
                        'Could not detect a supported package manager.\n\n'
                        'Supported package managers: apt, dnf, yum, pacman and zypper.'
                    ),
                    parent=root,
                )
                return
            run_commands_modal(parent=root, commands=commands)
        elif system == 'Darwin':
            if not is_root():
                messagebox.showwarning(
                    'Permissions required',
                    'To install requirements, please run this program with root/administrator privileges.',
                    parent=root,
                )
                return

            commands = [
                'xcode-select --install',
                'brew install freetype',
                'brew install fontconfig',
            ]
            run_commands_modal(parent=root, commands=commands)
        elif system == 'Windows':
            webbrowser.open(
                'https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-supported-redistributable-version'
            )
        else:
            messagebox.showerror(
                'Unsupported system',
                f'Unsupported operating system: {system}',
                parent=root,
            )

    def on_close(root: tk.Tk):
        root.destroy()
        sys.exit(0)

    root = tk.Tk()
    root.title('System Requirements')
    root.geometry('700x350')
    root.protocol('WM_DELETE_WINDOW', lambda: on_close(root))

    label = tk.Label(
        root, text='Maybe some required system requirements are missing'
    )
    label.pack(expand=True, fill='both', padx=12, pady=12)

    buttons = tk.Frame(root)
    buttons.pack(fill='x', padx=12, pady=(0, 12))

    tk.Button(
        buttons,
        text='Try run app',
        command=lambda: root.destroy(),
    ).pack(side='right')
    tk.Button(
        buttons,
        text='Install requirements',
        command=lambda: install_requirements(root),
    ).pack(side='right')
    root.mainloop()


def main() -> None:
    if is_root():
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox'

    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    db_manager = DBManager()
    db_manager.run_migrations()

    settings_repo = SettingsSQLRepo(db_manager=db_manager)
    settings = settings_repo.get().data
    if settings.theme == 'dark':
        dark(accent_color=settings.accent_color)
    elif settings.theme == 'light':
        light(accent_color=settings.accent_color)

    window = MainWindow(
        db_manager=db_manager,
        folders_repo=FoldersSQLRepo(db_manager=db_manager),
        requests_repo=RequestsSQLRepo(db_manager=db_manager),
        environments_repo=EnvironmentsSQLRepo(db_manager=db_manager),
        settings_repo=settings_repo,
    )
    window.show()

    fix_pyside_stylesheet(window=window, accent_color=settings.accent_color)

    with loop:
        loop.run_forever()


if __name__ == '__main__':
    show_requirements_popup()
    monkey_patch()
    main()
