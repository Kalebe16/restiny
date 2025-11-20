from __future__ import annotations

import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button

from restiny.entities import Environment
from restiny.widgets import PathChooser

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class _ImportFailedError(Exception):
    pass


class _ImportInvalidFileError(Exception):
    pass


class PostmanEnvironmentImportScreen(ModalScreen):
    app: RESTinyApp

    DEFAULT_CSS = """
    PostmanEnvironmentImportScreen {
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
                yield PathChooser.file(id='environment-file')
            with Horizontal(classes='w-auto h-auto'):
                yield Button('Cancel', classes='w-1fr', id='cancel')
                yield Button('Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)

        self.environment_file_chooser = self.query_one(
            '#environment-file', PathChooser
        )
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Postman environment import'

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self) -> None:
        self.dismiss(result=False)

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self) -> None:
        try:
            self._import()
        except _ImportInvalidFileError:
            self.notify('Invalid environment file', severity='error')
            return
        except _ImportFailedError:
            self.notify('Failed to import the environment', severity='error')
            return
        except Exception:
            self.notify(
                'Failed to import the environment; unexpected error',
                severity='error',
            )
            return

        self.notify(message='Environment imported', severity='information')
        self.dismiss(result=True)

    def _import(self) -> None:
        try:
            environment = json.loads(
                self.environment_file_chooser.path.read_text()
            )
        except Exception as error:
            raise _ImportInvalidFileError() from error

        variables = []
        for variable in environment['values']:
            variables.append(
                Environment.Variable(
                    enabled=variable['enabled'],
                    key=variable['key'],
                    value=variable['value'],
                )
            )

        create_environment_resp = self.app.environments_repo.create(
            environment=Environment(
                name=environment['name'], variables=variables
            )
        )
        if not create_environment_resp.ok:
            raise _ImportFailedError()
