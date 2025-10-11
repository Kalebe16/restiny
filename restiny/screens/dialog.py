from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDialogScreen(ModalScreen):
    DEFAULT_CSS = """
    ConfirmDialogScreen {
        align: center middle;
    }

    #modal-content {
        border: heavy black;
        border-title-color: gray;
        background: $surface;
        width: auto;
        height: auto;
        padding-top: 1;
        padding-left: 1;
        padding-right: 1;
    }

    #buttons-container {
        width: auto;
        height: auto;
        align-horizontal: right;
    }
    """

    BINDINGS = [Binding('escape', 'dismiss', show=False)]

    def __init__(
        self,
        title: str,
        text: str,
        confirm_label: str = 'Confirm',
        cancel_label: str = 'Cancel',
    ) -> None:
        super().__init__()
        self.title = title
        self.text = text
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-content'):
            yield Label(self.text)
            with Horizontal(id='buttons-container'):
                yield Button(self.cancel_label, flat=True, id='cancel')
                yield Button(self.confirm_label, flat=True, id='confirm')

    def on_mount(self) -> None:
        self.query_one('#modal-content').border_title = self.title

    @on(Button.Pressed, '#cancel')
    def cancel(self) -> None:
        self.dismiss(result=False)

    @on(Button.Pressed, '#confirm')
    def confirm(self) -> None:
        self.dismiss(result=True)


class InfoDialogScreen(ModalScreen):
    DEFAULT_CSS = """
    InfoDialogScreen {
        align: center middle;
    }

    #modal-content {
        border: heavy black;
        border-title-color: gray;
        background: $surface;
        width: auto;
        height: auto;
        padding-top: 1;
        padding-left: 1;
        padding-right: 1;
    }

    #button-container {
        width: 100%;
        height: auto;
        align-horizontal: right;
    }
    """

    BINDINGS = [Binding('escape', 'dismiss', show=False)]

    def __init__(self, title: str, text: str):
        super().__init__()
        self.title = title
        self.text = text

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-content'):
            yield Label(self.text)
            with Vertical(id='button-container'):
                yield Button('Ok', flat=True)

    def on_mount(self) -> None:
        self.query_one('#modal-content').border_title = self.title

    @on(Button.Pressed)
    def ok(self, message: Button.Pressed) -> None:
        self.dismiss()
