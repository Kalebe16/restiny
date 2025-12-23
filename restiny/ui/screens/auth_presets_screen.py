from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Label,
    ListView,
    Rule,
    Select,
    Switch,
)

from restiny.enums import AuthMode
from restiny.widgets.custom_input import CustomInput
from restiny.widgets.password_input import PasswordInput

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class AuthPresetsScreen(ModalScreen):
    app: RESTinyApp

    DEFAULT_CSS = """
    AuthPresetsScreen {
        align: center middle;
    }

    #modal-content {
        width: 70%;
        height: 80%;
        border: heavy black;
        border-title-color: gray;
        background: $surface;
    }

    Label {
        padding-left: 4;
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
            with Horizontal(classes='w-auto p-1'):
                with Vertical(classes='w-1fr h-auto'):
                    yield ListView(
                        classes='',
                        id='auth-presets',
                    )
                    with Horizontal(classes='w-auto h-auto mt-1'):
                        yield CustomInput(
                            placeholder='Auth preset name',
                            classes='w-4fr',
                            id='auth-preset-name',
                        )
                        yield Button(
                            label='➕',
                            tooltip='Add auth preset',
                            classes='',
                            id='add-auth-preset',
                        )

                yield Rule(orientation='vertical')

                with Vertical(classes='w-2fr h-auto'):
                    with Horizontal(classes='w-auto h-auto'):
                        yield CustomInput(
                            placeholder='Auth preset name',
                            classes='w-5fr',
                            id='auth-preset-rename',
                        )
                        yield Button(
                            '💾',
                            tooltip='Save auth preset',
                            classes='w-1fr',
                            id='save-auth-preset',
                        )
                        yield Button(
                            '➖',
                            tooltip='Delete auth preset',
                            classes='w-1fr',
                            id='delete-auth-preset',
                        )

                    with Horizontal(classes='h-auto mt-1'):
                        yield Switch(tooltip='Enabled', id='auth-enabled')
                        yield Select(
                            (
                                ('Basic', AuthMode.BASIC),
                                ('Bearer', AuthMode.BEARER),
                                ('API Key', AuthMode.API_KEY),
                                ('Digest', AuthMode.DIGEST),
                            ),
                            allow_blank=False,
                            tooltip='Auth mode',
                            id='auth-mode',
                        )
                    with ContentSwitcher(
                        initial='auth-basic', id='auth-mode-switcher'
                    ):
                        with Horizontal(id='auth-basic', classes='mt-1'):
                            yield CustomInput(
                                placeholder='Username',
                                select_on_focus=False,
                                classes='w-1fr',
                                id='auth-basic-username',
                            )
                            yield PasswordInput(
                                placeholder='Password',
                                select_on_focus=False,
                                classes='w-2fr',
                                id='auth-basic-password',
                            )
                        with Horizontal(id='auth-bearer', classes='mt-1'):
                            yield PasswordInput(
                                placeholder='Token',
                                select_on_focus=False,
                                id='auth-bearer-token',
                            )
                        with Horizontal(id='auth-api-key', classes='mt-1'):
                            yield Select(
                                (('Header', 'header'), ('Param', 'param')),
                                allow_blank=False,
                                tooltip='Where',
                                classes='w-1fr',
                                id='auth-api-key-where',
                            )
                            yield CustomInput(
                                placeholder='Key',
                                classes='w-2fr',
                                id='auth-api-key-key',
                            )
                            yield PasswordInput(
                                placeholder='Value',
                                classes='w-3fr',
                                id='auth-api-key-value',
                            )

                        with Horizontal(id='auth-digest', classes='mt-1'):
                            yield CustomInput(
                                placeholder='Username',
                                select_on_focus=False,
                                classes='w-1fr',
                                id='auth-digest-username',
                            )
                            yield PasswordInput(
                                placeholder='Password',
                                select_on_focus=False,
                                classes='w-2fr',
                                id='auth-digest-password',
                            )

                    yield Label(
                        "[i]Tip: You can use [b]'{{var}}'[/] or [b]'${var}'[/] to reference variables.[/]",
                        classes='mt-1',
                    )
            with Horizontal(classes='w-auto h-auto'):
                yield Button(label='Close', classes='w-1fr', id='close')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)
        self.auth_presets_list = self.query_one('#auth-presets', ListView)
        self.auth_preset_name_input = self.query_one(
            '#auth-preset-name', CustomInput
        )
        self.add_auth_preset_button = self.query_one(
            '#add-auth-preset', Button
        )
        self.auth_preset_rename_input = self.query_one(
            '#auth-preset-rename', CustomInput
        )
        self.auth_preset_save_button = self.query_one(
            '#save-auth-preset', Button
        )
        self.auth_preset_delete_button = self.query_one(
            '#delete-auth-preset', Button
        )

        self.close_button = self.query_one('#close', Button)

        self.modal_content.border_title = 'Auth presets'

    @on(Button.Pressed, '#close')
    def _on_close(self) -> None:
        self.dismiss(result=None)
