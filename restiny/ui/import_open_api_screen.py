from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button

from restiny.widgets import CustomInput, PathChooser

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class ImportOpenAPIScreen(ModalScreen):
    app: 'RESTinyApp'

    DEFAULT_CSS = """
    ImportOpenAPIScreen {
        align: center middle;
    }

    #modal-content {
        width: 30%;
        height: auto;
        border: heavy black;
        border-title-color: gray;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding(
            key='escape',
            action='dismiss',
            description='Quit the screen',
            show=False,
        ),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-content'):
            with Horizontal(classes='w-auto h-auto p-1'):
                yield CustomInput(
                    placeholder='Collection name',
                    select_on_focus=False,
                    id='collection-name',
                )
            with Horizontal(classes='w-auto h-auto p-1'):
                yield PathChooser.file(id='file')
            with Horizontal(classes='w-auto h-auto'):
                yield Button('Cancel', classes='w-1fr', id='cancel')
                yield Button('Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)

        self.collection_name_input = self.query_one(
            '#collection-name', CustomInput
        )
        self.file_chooser = self.query_one('#file', PathChooser)
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Import from openapi'
        self.file_chooser.allowed_file_suffixes = ['.yaml', '.yml', '.json']

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self, message: Button.Pressed) -> None:
        self.dismiss(result=None)

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self, message: Button.Pressed) -> None:
        if self.file_chooser.path.suffix not in ('.json', '.yaml', '.yml'):
            self.notify(message="Choose a valid file; '.json' or '.yaml/.yml'")
            return

        self.dismiss(
            result={
                'file': self.file_chooser.path,
                'collection_name': self.collection_name_input.value,
            }
        )
