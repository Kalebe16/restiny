import re
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._title_regex = (
            rf'^{self.BORDER_TITLE}\s+(?P<code>\d{{3}})\((?P<phrase>[^)]+)\)$'
        )
        self._subtitle_regex = r'^(?P<content_size>\d+)\s+bytes\s+in\s+(?P<elapsed_time>[\d.]+)\s+seconds$'

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

    @property
    def status(self) -> HTTPStatus | None:
        match = re.match(self._title_regex, self.border_title)
        if match:
            return HTTPStatus(int(match['code']))
        return None

    @status.setter
    def status(self, value: HTTPStatus) -> None:
        self.border_title = (
            f'{self.BORDER_TITLE} {value.value}({value.phrase})'
        )

    @property
    def content_size(self) -> int | None:
        match = re.match(self._subtitle_regex, self.border_subtitle)
        if match:
            return int(match['content_size'])
        return None

    @content_size.setter
    def content_size(self, value: int) -> None:
        match = re.match(self._subtitle_regex, self.border_subtitle)
        if match:
            elapsed_time = match['elapsed_time']
        else:
            elapsed_time = '0'

        self.border_subtitle = f'{value} bytes in {elapsed_time} seconds'

    @property
    def elapsed_time(self) -> float | None:
        match = re.match(self._subtitle_regex, self.border_subtitle)
        if match:
            return float(match['elapsed_time'])
        return None

    @elapsed_time.setter
    def elapsed_time(self, value: float) -> None:
        match = re.match(self._subtitle_regex, self.border_subtitle)
        if match:
            content_size = match['content_size']
        else:
            content_size = '0'

        self.border_subtitle = f'{content_size} bytes in {value} seconds'

    @property
    def headers(self) -> dict[str, str]:
        headers = {}
        for row_key in self.headers_data_table.rows:
            cells = self.headers_data_table.get_row(row_key)
            headers[cells[0]] = cells[1]
        return headers

    @headers.setter
    def headers(self, value: dict[str, str]) -> None:
        self.headers_data_table.clear()
        for header_key, header_value in value.items():
            self.headers_data_table.add_row(header_key, header_value)

    @property
    def body_raw_language(self) -> BodyRawLanguage:
        return self.body_raw_language_select.value

    @body_raw_language.setter
    def body_raw_language(self, value: BodyRawLanguage) -> None:
        self.body_raw_language_select.value = value

    @property
    def body_raw(self) -> str:
        return self.body_raw_editor.text

    @body_raw.setter
    def body_raw(self, value: str) -> None:
        self.body_raw_editor.text = value

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

    def clear(self) -> None:
        self.border_title = self.BORDER_TITLE
        self.border_subtitle = ''
        self.headers_data_table.clear()
        self.body_raw_language_select.value = BodyRawLanguage.PLAIN
        self.body_raw_editor.clear()

    @on(Select.Changed, '#body-raw-language')
    def _on_body_raw_language_changed(self, message: Select.Changed) -> None:
        self.body_raw_editor.language = self.body_raw_language_select.value
