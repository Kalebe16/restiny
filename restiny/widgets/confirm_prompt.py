from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmPrompt(ModalScreen):
    DEFAULT_CSS = """
    ConfirmPrompt {
        align: center middle;
    }

    #modal-content {
        border: heavy black;
        border-title-color: gray;
        background: $surface;
        width: auto;
        height: auto;
        max-width: 40%;
        text-align: center;
    }

    Horizontal {
        align: center middle;
    }

    #message {
    }
    """
    AUTO_FOCUS = '#confirm'

    BINDINGS = [
        Binding(
            key='escape',
            action='dismiss',
            description='Quit the screen',
            show=False,
        ),
    ]

    def __init__(self, message: str = 'Are you sure?') -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-content'):
            with Horizontal(classes='w-1fr h-auto mt-1'):
                yield Label(self._message, id='message')
            with Horizontal(classes='w-1fr h-auto mt-1'):
                yield Button(label='Cancel', classes='w-1fr', id='cancel')
                yield Button(label='Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)
        self.message_label = self.query_one('#message', Label)
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Confirm'

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self, message: Button.Pressed) -> None:
        self.dismiss(result=False)

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self, message: Button.Pressed) -> None:
        self.dismiss(result=True)
