import asyncio
from typing import Literal

import httpx
import pyperclip
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import Reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Select,
    Static,
    Switch,
    TabbedContent,
    LoadingIndicator
)

from data_fox.consts import HTTP_METHODS
from data_fox.widgets import (
    CustomTextArea,
    DynamicField,
    DynamicFields,
    PathChooser,
)


class URLArea(Static):
    BORDER_TITLE = 'URL'
    DEFAULT_CSS = """
    URLArea {
        layout: grid;
        grid-size: 3 1;
        grid-columns: 1fr 6fr 1fr;
        border: heavy black;
        height: 100%;
    }
    """

    request_pending = Reactive(False)

    class MakeRequest(Message):
        def __init__(self, method: str, url: str) -> None:
            self.method = method
            self.url = url
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Select.from_values(values=HTTP_METHODS, allow_blank=False)
        yield Input(placeholder='Enter URL')
        yield Button(label='Make request', classes='w-full')

    def on_mount(self) -> None:
        self.method_select = self.query_one(Select)
        self.url_input = self.query_one(Input)
        self.make_request_button = self.query_one(Button)

    @on(Button.Pressed)
    def on_make_request(self, message: Button.Pressed) -> None:
        self.post_message(
            message=self.MakeRequest(method=self.method, url=self.url)
        )

    @property
    def method(self) -> str:
        return self.method_select.value

    @method.setter
    def method(self, value: str) -> None:
        self.method_select.value = value

    @property
    def url(self) -> str:
        return self.url_input.value

    @url.setter
    def url(self, value: str) -> None:
        self.url_input.value = value

    def watch_request_pending(self, value: bool) -> None:
        if value is True:
            self.make_request_button.label = 'Cancel request'
            self.make_request_button.variant = 'error'
        elif value is False:
            self.make_request_button.label = 'Make request'
            self.make_request_button.variant = 'default'


class RequestArea(Static):
    BORDER_TITLE = 'Request'
    DEFAULT_CSS = """
    RequestArea {
        border: heavy black;
        height: 100%;
    }

    #body-section {
        layout: grid;
        grid-size: 1 2;
        grid-rows: auto 1fr; # First line takes up the necessary space, second takes up the rest
        grid-gutter: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent('Headers', 'Query params', 'Body'):
            yield DynamicFields(
                fields=[DynamicField(enabled=False, key='', value='')],
                id='headers-fields',
            )
            yield DynamicFields(
                fields=[DynamicField(enabled=False, key='', value='')],
                id='query-params-fields',
            )
            with Static(id='body-section'):
                with Horizontal(id='body-type-section'):
                    yield Switch(id='body-send-switch', tooltip='Send body?')
                    yield Select(
                        (
                            ('JSON', 'json'),
                            ('YAML', 'yaml'),
                            ('HTML', 'html'),
                            ('File', 'file'),
                        ),
                        allow_blank=False,
                        tooltip='Body type',
                        id='body-type-select',
                    )
                with Horizontal(id='body-editor-section', classes='hidden'):
                    yield CustomTextArea.code_editor(
                        language='json', id='body-editor'
                    )
                with Horizontal(id='body-file-section', classes='hidden'):
                    yield PathChooser(path_type='file', id='body-file-chooser')

    def on_mount(self) -> None:
        # TODO: Mudar nome do parametro pra evitar conflito com a property
        self.headers_fields: DynamicFields = self.query_one('#headers-fields')
        self.query_params_fields: DynamicFields = self.query_one(
            '#query-params-fields'
        )
        self.body_type_section: Horizontal = self.query_one(
            '#body-type-section'
        )
        self.should_send_body_switch: Switch = self.query_one(
            '#body-send-switch'
        )
        self.body_type_select: Select = self.query_one('#body-type-select')
        self.body_editor_section: Horizontal = self.query_one(
            '#body-editor-section'
        )
        self.body_editor: CustomTextArea = self.query_one('#body-editor')
        self.body_file_section: Horizontal = self.query_one(
            '#body-file-section'
        )
        self.body_file_chooser: PathChooser = self.query_one(
            '#body-file-chooser'
        )

    @on(Select.Changed, '#body-type-select')
    def on_change_body_type(self, message: Select.Changed) -> None:
        if message.value == 'file':
            self.toggle_body_type(type_to_show='file')
        else:
            self.toggle_body_type(type_to_show='editor')
            self.body_editor.language = message.value

    @property
    def headers(self) -> dict[str, str]:
        return self.headers_fields.values

    @property
    def query_params(self) -> dict[str, str]:
        return self.query_params_fields.values

    @property
    def should_send_body(self) -> bool:
        return self.should_send_body_switch.value

    @property
    def body_type(self) -> Literal['json', 'yaml', 'html', 'file']:
        return self.body_type_select.value.lower()

    @property
    def body(self) -> str | bytes:
        if self.body_type == 'file':
            if self.body_file_chooser.path:
                return self.body_file_chooser.path.read_bytes()
        else:
            return self.body_editor.text

    def toggle_body_type(
        self, type_to_show: Literal['editor', 'file']
    ) -> None:
        if type_to_show == 'editor':
            self.body_file_section.add_class('hidden')
            self.body_editor_section.remove_class('hidden')
        elif type_to_show == 'file':
            self.body_editor_section.add_class('hidden')
            self.body_file_section.remove_class('hidden')


class ResponseArea(Static):
    BORDER_TITLE = 'Response'
    DEFAULT_CSS = """
    ResponseArea {
        border: heavy black;
        height: 100%;
    }

    #body-section {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr auto;
        grid-rows: auto 1fr;
        grid-gutter: 1;
    }

    #body {
        column-span: 2;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent('Headers', 'Body'):
            with Static(id='headers-section'):
                yield CustomTextArea.code_editor(
                    id='headers', read_only=True, show_line_numbers=False
                )
            with Static(id='body-section'):
                yield Select(
                    (
                        ('Raw', None),
                        ('JSON', 'json'),
                        ('YAML', 'yaml'),
                        ('HTML', 'html'),
                    ),
                    allow_blank=False,
                    tooltip='Body type',
                    id='body-type-select',
                )
                yield Button('🔗', tooltip='Copy body', id='copy-body-button')
                yield CustomTextArea.code_editor(id='body', read_only=True)

    def on_mount(self) -> None:
        self.headers_section: Static = self.query_one('#headers-section')
        self.headers: CustomTextArea = self.query_one('#headers')
        self.body_section: Static = self.query_one('#body-section')
        self.body_type_select: Select = self.query_one('#body-type-select')
        self.copy_body_button: Button = self.query_one('#copy-body-button')
        self.body: CustomTextArea = self.query_one('#body')

    @on(Select.Changed, '#body-type-select')
    def on_body_type_changed(self, message: Select.Changed) -> None:
        self.body.language = self.body_type_select.value

    @on(Button.Pressed, '#copy-body-button')
    def on_copy_body(self, message: Button.Pressed) -> None:
        pyperclip.copy(text=self.body.text)
        self.notify('Copied body.')


class DataFoxApp(App, inherit_bindings=False):
    TITLE = 'DataFox'
    SUB_TITLE = (
        'A minimalist API client with the cunning simplicity of a fox 🦊'
    )
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = 'style.tcss'
    DEFAULT_CSS = """
    #main-content {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: auto 1fr;
        height: 100%;
    }

    URLArea {
        column-span: 2;
    }
    """
    BINDINGS = [
        ('escape', 'quit', 'Quit the app'),
        ('ctrl+t', 'toggle_dark_mode', 'Toggle dark mode'),
        ('f12', 'open_settings', 'Settings'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_client = httpx.AsyncClient()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Static(id='main-content'):
            yield URLArea()
            yield RequestArea()
            yield ResponseArea()
        yield Footer()

    def on_mount(self) -> None:
        self.url_area = self.query_one(URLArea)
        self.request_area = self.query_one(RequestArea)
        self.response_area = self.query_one(ResponseArea)

    def action_exit(self, *args, **kwargs) -> None:
        """
        Overrides `action_exit` to ensure the HTTP client is properly closed on app exit.

        This method closes the asynchronous HTTP client (`self.http_client`) used for requests throughout
        the app. Since `aclose()` is asynchronous, it typically requires `await`, but `action_exit` is a
        synchronous method. To handle this, we use `asyncio.run()` as a workaround to run the async
        cleanup within a synchronous context.

        `asyncio.run()` temporarily creates an event loop to execute `self.http_client.aclose()`, waits for it
        to complete, then shuts down the loop. This "mini-hack" ensures proper resource cleanup without
        refactoring `action_exit` to be asynchronous.
        """
        # Synchronously close the HTTP client
        asyncio.run(self.http_client.aclose())

        # Proceed with the default app exit process
        super().exit(*args, **kwargs)

    @on(URLArea.MakeRequest)
    def on_make_request(self, message: URLArea.MakeRequest) -> None:
        asyncio.create_task(self.fetch_data())

    async def fetch_data(self) -> None:
        """Makes an asynchronous HTTP request based on request_data and handles response."""
        method = self.url_area.method
        url = self.url_area.url
        headers = {
            header['key']: header['value']
            for header in self.request_area.headers
            if header['enabled']
        }
        query_params = {
            param['key']: param['value']
            for param in self.request_area.query_params
            if param['enabled']
        }

        # TODO: Avaliar uso da property `request_area.body`.
        file, body = None, None
        if self.request_area.should_send_body:
            if (
                self.request_area.body_type == 'file'
                and self.request_area.body_file_chooser.path
            ):
                file = self.request_area.body_file_chooser.path.read_bytes()
            else:
                body = self.request_area.body_editor.text
                if self.request_area.body_type == 'json':
                    headers['Content-Type'] = 'application/json'
                elif self.request_area.body_type == 'yaml':
                    headers['Content-Type'] = 'application/x-yaml'
                elif self.request_area.body_type == 'html':
                    headers['Content-Type'] = 'text/html'

        self.url_area.request_pending = True
        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                params=query_params,
                data=body,
                files={self.request_area.body_file_chooser.path.name: file}
                if file
                else None,
                timeout=100,
            )
        except httpx.RequestError as error:
            self.notify(
                f'{type(error).__name__}: {str(error)}', severity='error'
            )
        self.url_area.request_pending = False

        self.display_response(response=response)

    def display_response(self, response: httpx.Response) -> None:
        """Displays the response headers and body in the response area."""
        # Clear and display headers
        self.response_area.headers.clear()
        formatted_headers = ''
        for header_key, header_value in response.headers.items():
            formatted_headers += f'{header_key}: {header_value}\n'
        self.response_area.headers.insert(formatted_headers)

        # Clear display body
        self.response_area.body.clear()
        self.response_area.body.insert(response.text)

    def action_toggle_dark_mode(self) -> None:
        self.dark = not self.dark

        if self.request_area.body_editor.theme == 'monokai':
            self.request_area.body_editor.theme = 'github_light'
        elif self.request_area.body_editor.theme == 'github_light':
            self.request_area.body_editor.theme = 'monokai'

        if self.response_area.headers.theme == 'monokai':
            self.response_area.headers.theme = 'github_light'
        elif self.response_area.headers.theme == 'github_light':
            self.response_area.headers.theme = 'monokai'

        if self.response_area.body.theme == 'monokai':
            self.response_area.body.theme = 'github_light'
        elif self.response_area.body.theme == 'github_light':
            self.response_area.body.theme = 'monokai'

    # TODO: Criar modal para configurações globais
    def action_open_settings(self) -> None:
        pass
