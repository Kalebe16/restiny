import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # When running with pyinstaller
    MODULE_DIR = Path(sys._MEIPASS)
else:
    # When running without pyinstaller
    MODULE_DIR = Path(__file__).resolve().parent

CONF_DIR = Path.home().joinpath('.restiny')
DB_FILE = CONF_DIR / 'restiny.sqlite3'
