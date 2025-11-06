from enum import StrEnum


# TODO: Use http.HTTPMethod
class HTTPMethod(StrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    CONNECT = 'CONNECT'
    TRACE = 'TRACE'


class BodyMode(StrEnum):
    RAW = 'raw'
    FILE = 'file'
    FORM_URLENCODED = 'form_urlencoded'
    FORM_MULTIPART = 'form_multipart'


class BodyRawLanguage(StrEnum):
    PLAIN = ''
    HTML = 'html'
    JSON = 'json'
    YAML = 'yaml'
    XML = 'xml'


class ContentType(StrEnum):
    TEXT = 'text/plain'
    HTML = 'text/html'
    JSON = 'application/json'
    YAML = 'application/x-yaml'
    XML = 'application/xml'
    FORM_URLENCODED = 'application/x-www-form-urlencoded'
    FORM_MULTIPART = 'multipart/form-data'


class AuthMode(StrEnum):
    BASIC = 'basic'
    BEARER = 'bearer'
    API_KEY = 'api_key'
    DIGEST = 'digest'


class CustomThemes(StrEnum):
    DARK = 'dark'
    DRACULA = 'dracula'
    FOREST = 'forest'
