import sys
from pathlib import Path


def prepare_textual_dev_run() -> None:
    """
    Prepares the environment for running the app with `textual run --dev`
    """
    MODULE_PARENT_DIR = Path(__file__).parent.parent
    if str(MODULE_PARENT_DIR) not in sys.path:
        sys.path.append(str(MODULE_PARENT_DIR))


def run_app() -> None:
    import os
    import threading

    from restiny.data.db import DBManager
    from restiny.data.repos import (
        AuthPresetsSQLRepo,
        EnvironmentsSQLRepo,
        FoldersSQLRepo,
        RequestsSQLRepo,
        SettingsSQLRepo,
    )
    from restiny.ui.app import RESTinyApp

    db_manager = DBManager()
    db_manager.run_migrations()
    app = RESTinyApp(
        db_manager=db_manager,
        folders_repo=FoldersSQLRepo(db_manager=db_manager),
        requests_repo=RequestsSQLRepo(db_manager=db_manager),
        settings_repo=SettingsSQLRepo(db_manager=db_manager),
        environments_repo=EnvironmentsSQLRepo(db_manager=db_manager),
        auth_presets_repo=AuthPresetsSQLRepo(db_manager=db_manager),
    )

    if os.getenv('RESTINY_HEADLESS') == '1':
        # Runs in CI to ensure the app starts headlessly without crashing (smoke test).
        threading.Timer(10, lambda: app.exit()).start()
        app.run(headless=True)
    else:
        app.run()


def main() -> None:
    prepare_textual_dev_run()
    run_app()


if __name__ == '__main__':
    main()
