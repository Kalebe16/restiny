from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select

from restiny.entities import Settings
from restiny.enums import CustomThemes

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class SettingsScreen(ModalScreen):
    app: 'RESTinyApp'

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }

    #modal-content {
        width: auto;
        height: auto;
        max-width: 40%;
        border: heavy black;
        border-title-color: gray;
        background: $surface;
    }
    """
    AUTO_FOCUS = '#theme'

    BINDINGS = [
        Binding(
            key='escape',
            action='dismiss',
            description='Quit the screen',
            show=False,
        ),
    ]

    def compose(self) -> ComposeResult:
        settings = self.app.settings_repo.get().data
        with Vertical(id='modal-content'):
            with Horizontal(classes='w-auto h-auto mt-1 px-1'):
                yield Label('theme', classes='mt-1')
                yield Select(
                    [(theme.value, theme.value) for theme in CustomThemes],
                    value=settings.theme,
                    allow_blank=False,
                    id='theme',
                )
            with Horizontal(classes='w-auto h-auto mt-1'):
                yield Button(label='Cancel', classes='w-1fr', id='cancel')
                yield Button(label='Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)
        self.theme_select = self.query_one('#theme', Select)
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Settings'

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self, message: Button.Pressed) -> None:
        self.dismiss(result=False)

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self, message: Button.Pressed) -> None:
        self.app.settings_repo.set(Settings(theme=self.theme_select.value))
        self.dismiss(result=True)
