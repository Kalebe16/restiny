from enum import StrEnum


# TODO: Use http.HTTPMethod
class HTTPMethod(StrEnum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    CONNECT = 'CONNECT'
    TRACE = 'TRACE'

    @classmethod
    def values(cls):
        return [method.value for method in cls]


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
