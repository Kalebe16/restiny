import asyncio
import shutil
import subprocess
import sys

import qasync
from PySide6.QtWidgets import QApplication

from restiny.data.db import DBManager
from restiny.data.repos import (
    EnvironmentsSQLRepo,
    FoldersSQLRepo,
    RequestsSQLRepo,
    SettingsSQLRepo,
)
from restiny.themes import dark_amber, light_amber, system
from restiny.ui.app import MainWindow


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


def main() -> None:
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    db_manager = DBManager()
    db_manager.run_migrations()

    settings_repo = SettingsSQLRepo(db_manager=db_manager)
    settings = settings_repo.get().data

    if settings.theme == 'system':
        system(app)
    elif settings.theme == 'dark-amber':
        dark_amber(app)
    elif settings.theme == 'light-amber':
        light_amber(app)

    window = MainWindow(
        app=app,
        db_manager=db_manager,
        folders_repo=FoldersSQLRepo(db_manager=db_manager),
        requests_repo=RequestsSQLRepo(db_manager=db_manager),
        environments_repo=EnvironmentsSQLRepo(db_manager=db_manager),
        settings_repo=settings_repo,
    )
    window.show()

    with loop:
        loop.run_forever()


if __name__ == '__main__':
    monkey_patch()
    main()
