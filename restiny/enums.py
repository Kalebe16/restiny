from enum import Enum


# TODO: Use http.HTTPMethod
class HTTPMethod(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    CONNECT = 'CONNECT'
    TRACE = 'TRACE'


class BodyMode(str, Enum):
    RAW = 'raw'
    FILE = 'file'
    FORM_URLENCODED = 'form_urlencoded'
    FORM_MULTIPART = 'form_multipart'


class BodyRawLanguage(str, Enum):
    PLAIN = ''
    HTML = 'html'
    JSON = 'json'
    YAML = 'yaml'
    XML = 'xml'


class ContentType(str, Enum):
    TEXT = 'text/plain'
    HTML = 'text/html'
    JSON = 'application/json'
    YAML = 'application/x-yaml'
    XML = 'application/xml'
    FORM_URLENCODED = 'application/x-www-form-urlencoded'
    FORM_MULTIPART = 'multipart/form-data'


class AuthMode(str, Enum):
    BASIC = 'basic'
    BEARER = 'bearer'
    API_KEY = 'api_key'
    DIGEST = 'digest'
