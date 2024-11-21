import asyncio
import json
import mimetypes
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

from restiny.__about__ import __version__
from restiny.assets import STYLE_TCSS
from restiny.core import RequestArea, ResponseArea, URLArea
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
                with Vertical():
                    yield RequestArea()
                with Vertical():
                    yield ResponseArea()
        yield Footer()

    def on_mount(self) -> None:
        self.url_area = self.query_one(URLArea)
        self.request_area = self.query_one(RequestArea)
        self.response_area = self.query_one(ResponseArea)

    @on(DescendantFocus)
    def on_focus(self, event: DescendantFocus) -> None:
        self.last_focused_widget = event.widget
        last_focused_maximizable_area = self.find_maximizable_area_by_widget(
            widget=event.widget
        )
        if last_focused_maximizable_area:
            self.last_focused_maximizable_area = last_focused_maximizable_area

    @on(URLArea.SendRequest)
    def on_send_request(self, message: URLArea.SendRequest) -> None:
        self.response_area.reset_response()
        self.current_request = asyncio.create_task(self.send_request())

    @on(URLArea.CancelRequest)
    def on_cancel_request(self, message: URLArea.CancelRequest) -> None:
        if self.current_request and not self.current_request.done():
            self.current_request.cancel()

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
        for param in request_area_data.query_params:
            if not param.enabled:
                continue

            params[param.key] = param.value

        raw_body = None
        form_urlencoded = {}
        form_multipart = {}
        files = None
        if request_area_data.body.type == BodyMode.RAW:
            raw_body = request_area_data.body.payload
        elif request_area_data.body.type == BodyMode.FORM_URLENCODED:
            form_urlencoded = {
                form_field.key: form_field.value
                for form_field in request_area_data.body.payload
                if form_field.enabled
            }
        elif request_area_data.body.type == BodyMode.FORM_MULTIPART:
            form_multipart = {
                form_field.key: form_field.value
                for form_field in request_area_data.body.payload
                if form_field.enabled
            }
        elif request_area_data.body.type == BodyMode.FILE:
            files = [request_area_data.body.payload]

        curl_cmd = build_curl_cmd(
            method=method,
            url=url,
            headers=headers,
            params=params,
            raw_body=raw_body,
            form_urlencoded=form_urlencoded,
            form_multipart=form_multipart,
            files=files,
        )
        self.app.copy_to_clipboard(curl_cmd)
        pyperclip.copy(curl_cmd)
        self.notify(
            f'Command cURL copied to clipboard: `{curl_cmd}`',
            severity='information',
        )

    def find_maximizable_area_by_widget(self, widget: Widget) -> Widget | None:
        maximizable_areas: list[str] = [
            URLArea.__name__,
            RequestArea.__name__,
            ResponseArea.__name__,
        ]
        while widget is not None:
            if widget.__class__.__name__ in maximizable_areas:
                return widget
            widget = widget.parent

    async def send_request(self) -> None:
        url_area_data = self.url_area.get_data()
        request_area_data = self.request_area.get_data()

        headers: dict[str, str] = {
            header.key: header.value
            for header in request_area_data.headers
            if header.enabled
        }
        query_params: dict[str, str] = {
            param.key: param.value
            for param in request_area_data.query_params
            if param.enabled
        }

        self.response_area.loading = True
        self.url_area.request_pending = True
        try:
            async with httpx.AsyncClient(
                timeout=request_area_data.options.timeout,
                follow_redirects=request_area_data.options.follow_redirects,
                verify=request_area_data.options.verify_ssl,
            ) as http_client:
                request = None

                if not request_area_data.body.enabled:
                    request = http_client.build_request(
                        method=url_area_data.method,
                        url=url_area_data.url,
                        headers=headers,
                        params=query_params,
                    )
                else:
                    if request_area_data.body.type == BodyMode.RAW:
                        raw = request_area_data.body.payload

                        if (
                            request_area_data.body.raw_syntax
                            == BodyRawLanguage.JSON
                        ):
                            headers['content-type'] = ContentType.JSON
                            try:
                                raw = json.dumps(raw)
                            except Exception:
                                pass
                        elif (
                            request_area_data.body.raw_syntax
                            == BodyRawLanguage.YAML
                        ):
                            headers['content-type'] = ContentType.YAML
                        elif (
                            request_area_data.body.raw_syntax
                            == BodyRawLanguage.HTML
                        ):
                            headers['content-type'] = ContentType.HTML
                        elif (
                            request_area_data.body.raw_syntax
                            == BodyRawLanguage.XML
                        ):
                            headers['content-type'] = ContentType.XML
                        elif (
                            request_area_data.body.raw_syntax
                            == BodyRawLanguage.PLAIN
                        ):
                            headers['content-type'] = ContentType.TEXT

                        request = http_client.build_request(
                            method=url_area_data.method,
                            url=url_area_data.url,
                            headers=headers,
                            params=query_params,
                            content=raw,
                        )
                    elif request_area_data.body.type == BodyMode.FILE:
                        file = request_area_data.body.payload
                        headers['content-type'] = (
                            mimetypes.guess_type(file.name)[0]
                            or 'application/octet-stream'
                        )
                        request = http_client.build_request(
                            method=url_area_data.method,
                            url=url_area_data.url,
                            headers=headers,
                            params=query_params,
                            content=file.read_bytes(),
                        )
                    elif (
                        request_area_data.body.type == BodyMode.FORM_URLENCODED
                    ):
                        form_urlencoded = {
                            form_item.key: form_item.value
                            for form_item in request_area_data.body.payload
                            if form_item.enabled
                        }
                        request = http_client.build_request(
                            method=url_area_data.method,
                            url=url_area_data.url,
                            headers=headers,
                            params=query_params,
                            data=form_urlencoded,
                        )
                    elif (
                        request_area_data.body.type == BodyMode.FORM_MULTIPART
                    ):
                        form_multipart_str = {
                            form_item.key: form_item.value
                            for form_item in request_area_data.body.payload
                            if form_item.enabled
                            and isinstance(form_item.value, str)
                        }
                        form_multipart_files = {
                            form_item.key: (
                                form_item.value.name,
                                form_item.value.read_bytes(),
                                mimetypes.guess_type(form_item.value.name)[0]
                                or 'application/octet-stream',
                            )
                            for form_item in request_area_data.body.payload
                            if form_item.enabled
                            and isinstance(form_item.value, Path)
                        }
                        request = http_client.build_request(
                            method=url_area_data.method,
                            url=url_area_data.url,
                            headers=headers,
                            params=query_params,
                            data=form_multipart_str,
                            files=form_multipart_files,
                        )

                response = await http_client.send(request=request)
        except httpx.RequestError as error:
            error_name = type(error).__name__
            error_message = str(error)
            if error_message:
                self.notify(f'{error_name}: {error_message}', severity='error')
            else:
                self.notify(f'{error_name}', severity='error')
            self.response_area.has_response = False
        except asyncio.CancelledError:
            self.response_area.has_response = False
        else:
            self.display_response(response=response)
            self.response_area.has_response = True
        finally:
            self.response_area.loading = False
            self.url_area.request_pending = False

    def display_response(self, response: httpx.Response) -> None:
        def display_status() -> None:
            self.response_area.border_title = (
                f'Response - {response.status_code} {response.reason_phrase}'
            )

        def display_size_and_elapsed_time() -> None:
            self.response_area.border_subtitle = f'{response.num_bytes_downloaded} bytes in {response.elapsed.total_seconds():.2f} seconds'

        def display_headers() -> None:
            for header_key, header_value in response.headers.multi_items():
                self.response_area.headers_data_table.add_row(
                    header_key, header_value
                )

        def display_body() -> None:
            resp_content_type: str = response.headers.get('Content-Type', '')
            body_text_language = resp_content_type.rsplit('/')[1].lower()
            self.response_area.body_type_select.value = body_text_language
            self.response_area.body_text_area.language = body_text_language
            self.response_area.body_text_area.insert(response.text)
            self.response_area.body_text_area.scroll_home(
                animate=False, force=True, immediate=True
            )

        display_status()
        display_size_and_elapsed_time()
        display_headers()
        display_body()
