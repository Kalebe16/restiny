import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # When running with pyinstaller
    MODULE_DIR = Path(sys._MEIPASS)
else:
    # When running without pyinstaller
    MODULE_DIR = Path(__file__).resolve().parent

HOME_DIR = Path.home()
CONF_DIR = HOME_DIR / '.restiny'
CONF_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = CONF_DIR / 'restiny.sqlite3'
LOG_FILE = CONF_DIR / 'restiny.log'

DOWNLOADS_DIR = HOME_DIR / 'Downloads'
if not DOWNLOADS_DIR.exists():
    DOWNLOADS_DIR = CONF_DIR / 'downloads'
    DOWNLOADS_DIR.mkdir()
