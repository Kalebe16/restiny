from textual import on
from textual.app import ComposeResult
from textual.reactive import Reactive
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
    can_focus = True
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

    has_response: bool = Reactive(False, layout=True, init=True)

    def compose(self) -> ComposeResult:
        with ContentSwitcher(id='response-switcher', initial='no-content'):
            yield Label(
                "[i]No response yet. [/]Press [b]'Send Request'[/][i] to continue. 🚀[/]",
                id='no-content',
            )

            with TabbedContent(id='content'):
                with TabPane('Headers'):
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
                        tooltip='Body type',
                        id='body-type',
                    )
                    yield CustomTextArea.code_editor(
                        id='body', read_only=True, classes='mt-1'
                    )

    def on_mount(self) -> None:
        self._response_switcher = self.query_one(
            '#response-switcher', ContentSwitcher
        )

        self.headers_data_table = self.query_one('#headers', DataTable)
        self.body_type_select = self.query_one('#body-type', Select)
        self.body_text_area = self.query_one('#body', CustomTextArea)

        self.headers_data_table.add_columns('Key', 'Value')

    @on(Select.Changed, '#body-type')
    def on_body_type_changed(self, message: Select.Changed) -> None:
        self.body_text_area.language = self.body_type_select.value

    def watch_has_response(self, value: bool) -> None:
        if value is True:
            self._response_switcher.current = 'content'
        elif value is False:
            self._response_switcher.current = 'no-content'
            self.reset_response()

    def reset_response(self) -> None:
        self.border_title = self.BORDER_TITLE
        self.border_subtitle = ''
        self.headers_data_table.clear()
        self.body_type_select.value = BodyRawLanguage.PLAIN
        self.body_text_area.clear()
