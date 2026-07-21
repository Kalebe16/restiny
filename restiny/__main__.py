import asyncio
import platform
import shutil
import subprocess
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox


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


def show_requirements_popup() -> None:
    def install_requirements(root: tk.Tk) -> None:
        system = platform.system()
        if system == 'Linux':
            if shutil.which('apt'):
                command = (
                    'sudo apt install -y libxcb1; '
                    'sudo apt install -y libxcb-cursor0; '
                    'sudo apt install -y libxcb-xinerama0; '
                    'sudo apt install -y libxkbcommon-x11-0; '
                    'sudo apt install -y libgl1; '
                    'sudo apt install -y libegl1; '
                    'sudo apt install -y libnss3; '
                    'sudo apt install -y libasound2t64; '
                    'sudo apt install -y libasound2'
                )
            elif shutil.which('dnf'):
                command = (
                    'sudo dnf install -y libxcb; '
                    'sudo dnf install -y xcb-util-cursor; '
                    'sudo dnf install -y libxkbcommon-x11; '
                    'sudo dnf install -y mesa-libGL; '
                    'sudo dnf install -y mesa-libEGL; '
                    'sudo dnf install -y nss; '
                    'sudo dnf install -y alsa-lib'
                )
            elif shutil.which('yum'):
                command = (
                    'sudo yum install -y libxcb; '
                    'sudo yum install -y xcb-util-cursor; '
                    'sudo yum install -y libxkbcommon-x11; '
                    'sudo yum install -y mesa-libGL; '
                    'sudo yum install -y mesa-libEGL; '
                    'sudo yum install -y nss; '
                    'sudo yum install -y alsa-lib'
                )
            elif shutil.which('pacman'):
                command = (
                    'sudo pacman -Syu --needed libxcb; '
                    'sudo pacman -S --needed xcb-util-cursor; '
                    'sudo pacman -S --needed libxkbcommon-x11; '
                    'sudo pacman -S --needed mesa; '
                    'sudo pacman -S --needed nss; '
                    'sudo pacman -S --needed alsa-lib'
                )
            elif shutil.which('zypper'):
                command = (
                    'sudo zypper install -y libxcb1; '
                    'sudo zypper install -y libxcb-cursor0; '
                    'sudo zypper install -y libxkbcommon-x11-0; '
                    'sudo zypper install -y Mesa-libGL1; '
                    'sudo zypper install -y Mesa-libEGL1; '
                    'sudo zypper install -y mozilla-nss; '
                    'sudo zypper install -y alsa'
                )
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
            open_linux_terminal(command=command)
        elif system == 'Darwin':
            command = (
                'xcode-select --install; brew install freetype fontconfig'
            )
            open_darwin_terminal(command=command)
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
        command=root.destroy,
    ).pack(side='right')
    tk.Button(
        buttons,
        text='Install requirements',
        command=lambda: install_requirements(root),
    ).pack(side='right')
    root.mainloop()


def main() -> None:
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
    )

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
