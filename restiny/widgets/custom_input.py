from textual import on
from textual.binding import Binding
from textual.events import Blur
from textual.widgets import Input


class CustomInput(Input):
    BINDINGS = [
        Binding(
            key='ctrl+a',
            action='select_all',
            description='Select all text',
            show=False,
        ),
    ]

    @on(Blur)
    def on_blur(self, event: Blur) -> None:
        self.selection = 0, 0
        self.cursor_position = len(self.value)
