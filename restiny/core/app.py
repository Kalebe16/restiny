import asyncio
import json
import mimetypes
from http import HTTPStatus
from pathlib import Path

import httpx
import pyperclip
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import DescendantFocus
from textual.widget import Widget
from textual.widgets import Footer, Header

from restiny import httpx_auths
from restiny.__about__ import __version__
from restiny.assets import STYLE_TCSS
from restiny.core import (
    RequestArea,
    RequestAreaData,
    ResponseArea,
    URLArea,
    URLAreaData,
)
from restiny.core.request_area import (
    APIKeyAuth,
    BasicAuth,
    BearerAuth,
    DigestAuth,
)
from restiny.core.response_area import ResponseAreaData
from restiny.enums import BodyMode, BodyRawLanguage, ContentType
from restiny.utils import build_curl_cmd


class RESTinyApp(App, inherit_bindings=False):
    TITLE = f'RESTiny v{__version__}'
    SUB_TITLE = 'Minimal HTTP client, no bullshit'
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = STYLE_TCSS
    BINDINGS = [
        Binding(
            key='escape', action='quit', description='Quit the app', show=True
        ),
        Binding(
            key='f10',
            action='maximize_or_minimize_area',
            description='Maximize/Minimize area',
            show=True,
        ),
        Binding(
            key='f9',
            action='copy_as_curl',
            description='Copy as curl',
            show=True,
        ),
    ]
    theme = 'textual-dark'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current_request: asyncio.Task | None = None
        self.last_focused_widget: Widget | None = None
        self.last_focused_maximizable_area: Widget | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id='main-content'):
            with Horizontal(classes='h-auto'):
                yield URLArea()
            with Horizontal(classes='h-1fr'):
                yield RequestArea()
                yield ResponseArea()
        yield Footer()

    def on_mount(self) -> None:
        self.url_area = self.query_one(URLArea)
        self.request_area = self.query_one(RequestArea)
        self.response_area = self.query_one(ResponseArea)

    def action_maximize_or_minimize_area(self) -> None:
        if self.screen.maximized:
            self.screen.minimize()
        else:
            self.screen.maximize(self.last_focused_maximizable_area)

    def action_copy_as_curl(self) -> None:
        url_area_data = self.url_area.get_data()
        request_area_data = self.request_area.get_data()

        method = url_area_data.method
        url = url_area_data.url

        headers = {}
        for header in request_area_data.headers:
            if not header.enabled:
                continue

            headers[header.key] = header.value

        params = {}
        for param in request_area_data.params:
            if not param.enabled:
                continue

            params[param.key] = param.value

        body_raw = None
        body_form_urlencoded = {}
        body_form_multipart = {}
        body_files = None
        if request_area_data.body.enabled:
            if request_area_data.body.mode == BodyMode.RAW:
                body_raw = request_area_data.body.payload
            elif request_area_data.body.mode == BodyMode.FORM_URLENCODED:
                body_form_urlencoded = {
                    form_field.key: form_field.value
                    for form_field in request_area_data.body.payload
                    if form_field.enabled
                }
            elif request_area_data.body.mode == BodyMode.FORM_MULTIPART:
                body_form_multipart = {
                    form_field.key: form_field.value
                    for form_field in request_area_data.body.payload
                    if form_field.enabled
                }
            elif request_area_data.body.mode == BodyMode.FILE:
                body_files = [request_area_data.body.payload]

        auth_basic = None
        auth_bearer = None
        auth_api_key_header = None
        auth_api_key_param = None
        auth_digest = None
        if request_area_data.auth.enabled:
            if isinstance(request_area_data.auth.value, BasicAuth):
                auth_basic = (
                    request_area_data.auth.value.username,
                    request_area_data.auth.value.password,
                )
            elif isinstance(request_area_data.auth.value, BearerAuth):
                auth_bearer = request_area_data.auth.value.token
            elif isinstance(request_area_data.auth.value, APIKeyAuth):
                if request_area_data.auth.value.where == 'header':
                    auth_api_key_header = (
                        request_area_data.auth.value.key,
                        request_area_data.auth.value.value,
                    )
                elif request_area_data.auth.value.where == 'param':
                    auth_api_key_param = (
                        request_area_data.auth.value.key,
                        request_area_data.auth.value.value,
                    )
            elif isinstance(request_area_data.auth.value, DigestAuth):
                auth_digest = (
                    request_area_data.auth.value.username,
                    request_area_data.auth.value.password,
                )

        curl_cmd = build_curl_cmd(
            method=method,
            url=url,
            headers=headers,
            params=params,
            body_raw=body_raw,
            body_form_urlencoded=body_form_urlencoded,
            body_form_multipart=body_form_multipart,
            body_files=body_files,
            auth_basic=auth_basic,
            auth_bearer=auth_bearer,
            auth_api_key_header=auth_api_key_header,
            auth_api_key_param=auth_api_key_param,
            auth_digest=auth_digest,
        )
        self.copy_to_clipboard(curl_cmd)
        self.notify(
            'Command CURL copied to clipboard',
            severity='information',
        )

    def copy_to_clipboard(self, text: str) -> None:
        super().copy_to_clipboard(text)
        try:
            # Also copy to the system clipboard (outside of the app)
            pyperclip.copy(text)
        except Exception:
            pass

    @on(DescendantFocus)
    def _on_focus(self, event: DescendantFocus) -> None:
        self.last_focused_widget = event.widget
        last_focused_maximizable_area = self._find_maximizable_area_by_widget(
            widget=event.widget
        )
        if last_focused_maximizable_area:
            self.last_focused_maximizable_area = last_focused_maximizable_area

    @on(URLArea.SendRequest)
    def _on_send_request(self, message: URLArea.SendRequest) -> None:
        self.current_request = asyncio.create_task(self._send_request())

    @on(URLArea.CancelRequest)
    def _on_cancel_request(self, message: URLArea.CancelRequest) -> None:
        if self.current_request and not self.current_request.done():
            self.current_request.cancel()

    def _find_maximizable_area_by_widget(
        self, widget: Widget
    ) -> Widget | None:
        while widget is not None:
            if (
                isinstance(widget, URLArea)
                or isinstance(widget, RequestArea)
                or isinstance(widget, ResponseArea)
            ):
                return widget
            widget = widget.parent

    async def _send_request(self) -> None:
        url_area_data = self.url_area.get_data()
        request_area_data = self.request_area.get_data()

        self.response_area.set_data(data=None)
        self.response_area.loading = True
        self.url_area.request_pending = True
        try:
            async with httpx.AsyncClient(
                timeout=request_area_data.options.timeout,
                follow_redirects=request_area_data.options.follow_redirects,
                verify=request_area_data.options.verify_ssl,
            ) as http_client:
                request = self._build_request(
                    http_client=http_client,
                    url_area_data=url_area_data,
                    request_area_data=request_area_data,
                )
                auth = self._build_auth(
                    request_area_data=request_area_data,
                )
                response = await http_client.send(request=request, auth=auth)
                self._display_response(response=response)
                self.response_area.is_showing_response = True
        except httpx.RequestError as error:
            error_name = type(error).__name__
            error_message = str(error)
            if error_message:
                self.notify(f'{error_name}: {error_message}', severity='error')
            else:
                self.notify(f'{error_name}', severity='error')
            self.response_area.set_data(data=None)
            self.response_area.is_showing_response = False
        except asyncio.CancelledError:
            self.response_area.set_data(data=None)
            self.response_area.is_showing_response = False
        finally:
            self.response_area.loading = False
            self.url_area.request_pending = False

    def _build_request(
        self,
        http_client: httpx.AsyncClient,
        url_area_data: URLAreaData,
        request_area_data: RequestAreaData,
    ) -> tuple[httpx.Request, httpx.Auth | None]:
        headers: dict[str, str] = {
            header.key: header.value
            for header in request_area_data.headers
            if header.enabled
        }
        params: dict[str, str] = {
            param.key: param.value
            for param in request_area_data.params
            if param.enabled
        }

        if not request_area_data.body.enabled:
            return http_client.build_request(
                method=url_area_data.method,
                url=url_area_data.url,
                headers=headers,
                params=params,
            )

        if request_area_data.body.mode == BodyMode.RAW:
            raw_language_to_content_type = {
                BodyRawLanguage.JSON: ContentType.JSON,
                BodyRawLanguage.YAML: ContentType.YAML,
                BodyRawLanguage.HTML: ContentType.HTML,
                BodyRawLanguage.XML: ContentType.XML,
                BodyRawLanguage.PLAIN: ContentType.TEXT,
            }
            headers['content-type'] = raw_language_to_content_type.get(
                request_area_data.body.raw_language, ContentType.TEXT
            )

            raw = request_area_data.body.payload
            if headers['content-type'] == ContentType.JSON:
                try:
                    raw = json.dumps(raw)
                except Exception:
                    pass

            return http_client.build_request(
                method=url_area_data.method,
                url=url_area_data.url,
                headers=headers,
                params=params,
                content=raw,
            )
        elif request_area_data.body.mode == BodyMode.FILE:
            file = request_area_data.body.payload
            if 'content-type' not in headers:
                headers['content-type'] = (
                    mimetypes.guess_type(file.name)[0]
                    or 'application/octet-stream'
                )
            return http_client.build_request(
                method=url_area_data.method,
                url=url_area_data.url,
                headers=headers,
                params=params,
                content=file.read_bytes(),
            )
        elif request_area_data.body.mode == BodyMode.FORM_URLENCODED:
            form_urlencoded = {
                form_item.key: form_item.value
                for form_item in request_area_data.body.payload
                if form_item.enabled
            }
            return http_client.build_request(
                method=url_area_data.method,
                url=url_area_data.url,
                headers=headers,
                params=params,
                data=form_urlencoded,
            )
        elif request_area_data.body.mode == BodyMode.FORM_MULTIPART:
            form_multipart_str = {
                form_item.key: form_item.value
                for form_item in request_area_data.body.payload
                if form_item.enabled and isinstance(form_item.value, str)
            }
            form_multipart_files = {
                form_item.key: (
                    form_item.value.name,
                    form_item.value.read_bytes(),
                    mimetypes.guess_type(form_item.value.name)[0]
                    or 'application/octet-stream',
                )
                for form_item in request_area_data.body.payload
                if form_item.enabled and isinstance(form_item.value, Path)
            }
            return http_client.build_request(
                method=url_area_data.method,
                url=url_area_data.url,
                headers=headers,
                params=params,
                data=form_multipart_str,
                files=form_multipart_files,
            )

    def _build_auth(
        self,
        request_area_data: RequestAreaData,
    ) -> httpx.Auth | None:
        auth = request_area_data.auth

        if not auth.enabled:
            return

        if isinstance(auth.value, BasicAuth):
            return httpx.BasicAuth(
                username=auth.value.username,
                password=auth.value.password,
            )
        elif isinstance(auth.value, BearerAuth):
            return httpx_auths.BearerAuth(token=auth.value.token)
        elif isinstance(auth.value, APIKeyAuth):
            if auth.value.where == 'header':
                return httpx_auths.APIKeyHeaderAuth(
                    key=auth.value.key, value=auth.value.value
                )
            elif auth.value.where == 'param':
                return httpx_auths.APIKeyParamAuth(
                    key=auth.value.key, value=auth.value.value
                )
        elif isinstance(auth.value, DigestAuth):
            return httpx.DigestAuth(
                username=auth.value.username,
                password=auth.value.password,
            )

    def _display_response(self, response: httpx.Response) -> None:
        status = HTTPStatus(response.status_code)
        size = response.num_bytes_downloaded
        elapsed_time = round(response.elapsed.total_seconds(), 2)
        headers = {
            header_key: header_value
            for header_key, header_value in response.headers.multi_items()
        }
        content_type_to_body_language = {
            ContentType.TEXT: BodyRawLanguage.PLAIN,
            ContentType.HTML: BodyRawLanguage.HTML,
            ContentType.JSON: BodyRawLanguage.JSON,
            ContentType.YAML: BodyRawLanguage.YAML,
            ContentType.XML: BodyRawLanguage.XML,
        }
        body_raw_language = content_type_to_body_language.get(
            response.headers.get('Content-Type'), BodyRawLanguage.PLAIN
        )
        body_raw = response.text
        self.response_area.set_data(
            data=ResponseAreaData(
                status=status,
                size=size,
                elapsed_time=elapsed_time,
                headers=headers,
                body_raw_language=body_raw_language,
                body_raw=body_raw,
            )
        )
