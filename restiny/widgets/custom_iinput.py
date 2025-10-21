from textual import on
from textual.binding import Binding
from textual.events import Blur
from textual.widgets import Input


class CustomInput(Input):
    BINDINGS = [
        Binding('ctrl+a', 'select_all', 'Select all text'),
    ]

    @on(Blur)
    def on_blur(self, event: Blur) -> None:
        self.selection = 0, 0
        self.cursor_position = len(self.value)
