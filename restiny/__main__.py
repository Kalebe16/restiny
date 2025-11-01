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
    from restiny.consts import CONF_DIR, DB_FILE
    from restiny.data.db import DBManager
    from restiny.data.repos import FoldersSQLRepo, RequestsSQLRepo
    from restiny.ui.app import RESTinyApp

    CONF_DIR.mkdir(exist_ok=True)
    DB_FILE.touch(exist_ok=True)
    db_manager = DBManager(db_url=f'sqlite:///{DB_FILE}')
    db_manager.run_migrations()
    RESTinyApp(
        folders_repo=FoldersSQLRepo(db_manager=db_manager),
        requests_repo=RequestsSQLRepo(db_manager=db_manager),
    ).run()


def main() -> None:
    prepare_textual_dev_run()
    run_app()


if __name__ == '__main__':
    main()
