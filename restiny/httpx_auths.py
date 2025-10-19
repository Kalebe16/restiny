from collections.abc import Generator

import httpx


class BearerAuth(httpx.Auth):
    """
    Adds a Bearer token to the Authorization header of each request.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response]:
        request.headers['authorization'] = f'Bearer {self._token}'
        yield request


class APIKeyHeaderAuth(httpx.Auth):
    """
    Adds an API key to the request headers.
    """

    def __init__(self, key: str, value: str) -> None:
        self._key = key
        self._value = value

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response]:
        request.headers[self._key] = self._value
        yield request


class APIKeyParamAuth(httpx.Auth):
    """
    Adds an API key as a query parameter to the request URL.
    """

    def __init__(self, key: str, value: str) -> None:
        self._key = key
        self._value = value

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response]:
        request.url = request.url.copy_with(
            params=request.url.params.set(self._key, self._value)
        )
        yield request
