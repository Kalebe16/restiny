from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button

from restiny.logger import get_logger
from restiny.widgets import PathChooser

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


logger = get_logger()


class _ImportFailedError(Exception):
    pass


class _ImportInvalidFileError(Exception):
    pass


class OpenapiSpecImportScreen(ModalScreen):
    app: RESTinyApp

    DEFAULT_CSS = """
    OpenapiSpecImportScreen {
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
                yield PathChooser.file(
                    id='open-api-spec-file',
                    allowed_file_suffixes=['.json', '.yaml', '.yml'],
                )
            with Horizontal(classes='w-auto h-auto'):
                yield Button('Cancel', classes='w-1fr', id='cancel')
                yield Button('Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)

        self.openapi_spec_file_chooser = self.query_one(
            '#open-api-spec-file', PathChooser
        )
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Openapi spec import'

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self) -> None:
        self.dismiss(result=False)

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self) -> None:
        try:
            self._import()
        except _ImportInvalidFileError:
            self.notify('Invalid openapi spec file', severity='error')
            return
        except _ImportFailedError:
            self.notify('Failed to import the openapi spec', severity='error')
            return
        except Exception:
            self.notify(
                'Failed to import the openapi spec; unexpected error',
                severity='error',
            )
            logger.exception('Failed to import the openapi spec')
            return

        self.notify(message='Openapi spec imported', severity='information')
        self.dismiss(result=True)

    def _import(self) -> None:
        pass
