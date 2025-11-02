from dataclasses import dataclass
from http import HTTPStatus

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import (
    ContentSwitcher,
    DataTable,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from restiny.enums import BodyRawLanguage
from restiny.widgets import CustomTextArea


@dataclass
class ResponseAreaData:
    status: HTTPStatus
    size: int
    elapsed_time: float | int
    headers: dict
    body_raw_language: BodyRawLanguage
    body_raw: str


# TODO: Implement 'Trace' tab pane
class ResponseArea(Static):
    ALLOW_MAXIMIZE = True
    focusable = True
    BORDER_TITLE = 'Response'
    DEFAULT_CSS = """
    ResponseArea {
        width: 1fr;
        height: 1fr;
        border: heavy black;
        border-title-color: gray;
        border-subtitle-color: gray;
        padding: 1;
    }

    #no-content {
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    """

    def compose(self) -> ComposeResult:
        with ContentSwitcher(id='response-switcher', initial='no-content'):
            yield Label(
                "[i]No response yet. [/]Press [b]'Send Request'[/][i] to continue. 🚀[/]",
                id='no-content',
            )

            with TabbedContent(id='content'):
                with TabPane('Headers'):
                    with VerticalScroll():
                        yield DataTable(show_cursor=False, id='headers')
                with TabPane('Body'):
                    yield Select(
                        (
                            ('Plain', BodyRawLanguage.PLAIN),
                            ('HTML', BodyRawLanguage.HTML),
                            ('JSON', BodyRawLanguage.JSON),
                            ('YAML', BodyRawLanguage.YAML),
                            ('XML', BodyRawLanguage.XML),
                        ),
                        allow_blank=False,
                        tooltip='Syntax highlighting for the response body',
                        id='body-raw-language',
                    )
                    yield CustomTextArea.code_editor(
                        id='body-raw', read_only=True, classes='mt-1'
                    )

    def on_mount(self) -> None:
        self._response_switcher = self.query_one(
            '#response-switcher', ContentSwitcher
        )

        self.headers_data_table = self.query_one('#headers', DataTable)
        self.body_raw_language_select = self.query_one(
            '#body-raw-language', Select
        )
        self.body_raw_editor = self.query_one('#body-raw', CustomTextArea)

        self.headers_data_table.add_columns('Key', 'Value')

    def set_data(self, data: ResponseAreaData | None) -> None:
        self.border_title = self.BORDER_TITLE
        self.border_subtitle = ''
        self.headers_data_table.clear()
        self.body_raw_language_select.value = BodyRawLanguage.PLAIN
        self.body_raw_editor.clear()

        if data is None:
            return

        self.border_title = f'Response - {data.status} {data.status.phrase}'
        self.border_subtitle = (
            f'{data.size} bytes in {data.elapsed_time} seconds'
        )
        for header_key, header_value in data.headers.items():
            self.headers_data_table.add_row(header_key, header_value)
        self.body_raw_language_select.value = data.body_raw_language
        self.body_raw_editor.text = data.body_raw

    @property
    def is_showing_response(self) -> bool:
        if self._response_switcher.current == 'content':
            return True
        elif self._response_switcher.current == 'no-content':
            return False

    @is_showing_response.setter
    def is_showing_response(self, value: bool) -> None:
        if value is True:
            self._response_switcher.current = 'content'
        elif value is False:
            self._response_switcher.current = 'no-content'

    @on(Select.Changed, '#body-raw-language')
    def _on_body_raw_language_changed(self, message: Select.Changed) -> None:
        self.body_raw_editor.language = self.body_raw_language_select.value
