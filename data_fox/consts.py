from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent

# TODO: Transform this in a enum
HTTP_METHODS = (
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'HEAD',
    'OPTIONS',
    'PATCH',
    'CONNECT',
    'TRACE',
)
