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
    ListItem,
    ListView,
    Rule,
    Select,
)

from restiny.entities import AuthPreset
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

    #auth-empty {
        align: center middle;
        text-align: center;
        content-align: center middle;
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

                with ContentSwitcher(
                    initial='auth-empty',
                    id='auth-content-switcher',
                    classes='w-2fr',
                ):
                    yield Label(
                        '[italic]No auth preset selected[/]',
                        id='auth-empty',
                    )

                    with Vertical(id='auth-content'):
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

    async def on_mount(self) -> None:
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

        self.auth_content_switcher = self.query_one(
            '#auth-content-switcher', ContentSwitcher
        )

        self.auth_mode_select = self.query_one('#auth-mode', Select)
        self.auth_mode_switcher = self.query_one(
            '#auth-mode-switcher', ContentSwitcher
        )

        self.auth_basic_username_input = self.query_one(
            '#auth-basic-username', CustomInput
        )
        self.auth_basic_password_input = self.query_one(
            '#auth-basic-password', PasswordInput
        )

        self.auth_bearer_token_input = self.query_one(
            '#auth-bearer-token', PasswordInput
        )

        self.auth_api_key_key_input = self.query_one(
            '#auth-api-key-key', CustomInput
        )
        self.auth_api_key_value_input = self.query_one(
            '#auth-api-key-value', PasswordInput
        )
        self.auth_api_key_where_select = self.query_one(
            '#auth-api-key-where', Select
        )

        self.auth_digest_username_input = self.query_one(
            '#auth-digest-username', CustomInput
        )
        self.auth_digest_password_input = self.query_one(
            '#auth-digest-password', PasswordInput
        )

        self.close_button = self.query_one('#close', Button)

        self.modal_content.border_title = 'Auth presets'

        await self._populate_auth_presets()

    @property
    def _selected_auth_preset_id(self) -> str | None:
        if self.auth_presets_list.index is None:
            return None

        return self.auth_presets_list.children[
            self.auth_presets_list.index
        ].id.removeprefix('auth-preset-')

    @property
    def _selected_auth_preset_name(self) -> str | None:
        if self.auth_presets_list.index is None:
            return None

        return (
            self.auth_presets_list.children[self.auth_presets_list.index]
            .children[0]
            .content
        )

    @on(Select.Changed, '#auth-mode')
    def _on_change_auth_mode(self, message: Select.Changed) -> None:
        if message.value == 'basic':
            self.auth_mode_switcher.current = 'auth-basic'
        elif message.value == 'bearer':
            self.auth_mode_switcher.current = 'auth-bearer'
        elif message.value == 'api_key':
            self.auth_mode_switcher.current = 'auth-api-key'
        elif message.value == 'digest':
            self.auth_mode_switcher.current = 'auth-digest'

    @on(ListView.Selected, '#auth-presets')
    async def _on_select_auth_preset(self) -> None:
        self.auth_content_switcher.current = 'auth-content'

        auth_preset = self.app.auth_presets_repo.get_by_id(
            id=self._selected_auth_preset_id
        ).data

        self.auth_preset_rename_input.value = auth_preset.name
        self.auth_mode_select.value = auth_preset.auth_mode

        if auth_preset.auth_mode == AuthMode.BASIC:
            self.auth_basic_username_input.value = auth_preset.auth.username
            self.auth_basic_password_input.value = auth_preset.auth.password
        elif auth_preset.auth_mode == AuthMode.BEARER:
            self.auth_bearer_token_input.value = auth_preset.auth.token
        elif auth_preset.auth_mode == AuthMode.API_KEY:
            self.auth_api_key_key_input.value = auth_preset.auth.key
            self.auth_api_key_value_input.value = auth_preset.auth.value
        elif auth_preset.auth_mode == AuthMode.DIGEST:
            self.auth_digest_username_input = auth_preset.auth.username
            self.auth_digest_password_input = auth_preset.auth.password

    @on(Button.Pressed, '#add-auth-preset')
    @on(CustomInput.Submitted, '#auth-preset-name')
    async def _on_add_auth_preset(self) -> None:
        if not self.auth_preset_name_input.value.strip():
            self.notify('Auth Preset name is required', severity='error')
            return

        create_resp = self.app.auth_presets_repo.create(
            AuthPreset(
                name=self.auth_preset_name_input.value,
                auth_mode=AuthMode.BASIC,
                auth=AuthPreset.BasicAuth(username='', password=''),
            )
        )
        if not create_resp.ok:
            self.notify(
                f'Failed to create Auth Preset ({create_resp.status})',
                severity='error',
            )
            return

        await self._add_auth_preset(
            name=create_resp.data.name, id=create_resp.data.id
        )
        self.auth_preset_name_input.value = ''
        self.auth_presets_list.index = len(self.auth_presets_list.children) - 1
        await self._on_select_auth_preset()
        self.notify('Auth Preset added', severity='information')

        self.app.request_area.populate_auths()

    @on(Button.Pressed, '#save-auth-preset')
    @on(CustomInput.Submitted, '#auth-preset-rename')
    async def _on_save_auth_preset(self) -> None:
        if not self.auth_preset_rename_input.value.strip():
            self.notify('Auth preset name is required', severity='error')
            return

        auth_mode = self.auth_mode_select.value
        auth = None
        if auth_mode == AuthMode.BASIC:
            auth = AuthPreset.BasicAuth(
                username=self.auth_basic_username_input.value,
                password=self.auth_basic_password_input.value,
            )
        elif auth_mode == AuthMode.BEARER:
            auth = AuthPreset.BearerAuth(
                token=self.auth_bearer_token_input.value
            )
        elif auth_mode == AuthMode.API_KEY:
            auth = AuthPreset.ApiKeyAuth(
                key=self.auth_api_key_key_input.value,
                value=self.auth_api_key_value_input.value,
                where=self.auth_api_key_where_select.value,
            )
        elif auth_mode == AuthMode.DIGEST:
            auth = AuthPreset.DigestAuth(
                username=self.auth_digest_username_input.value,
                password=self.auth_digest_password_input.value,
            )
        update_resp = self.app.auth_presets_repo.update(
            AuthPreset(
                id=self._selected_auth_preset_id,
                name=self.auth_preset_rename_input.value,
                auth_mode=auth_mode,
                auth=auth,
            )
        )
        if not update_resp.ok:
            self.notify(
                f'Failed to update Auth Preset ({update_resp.status})',
                severity='error',
            )
            return

        self.auth_presets_list.children[self.auth_presets_list.index].children[
            0
        ].update(update_resp.data.name)
        self.notify('Auth Preset updated', severity='information')

        self.app.request_area.populate_auths()

    @on(Button.Pressed, '#delete-auth-preset')
    async def _on_remove_auth_preset(self) -> None:
        if self.auth_presets_list.index is None:
            self.notify('No Auth Preset selected', severity='error')
            return

        self.app.auth_presets_repo.delete_by_id(self._selected_auth_preset_id)
        focus_target_index = max(0, self.auth_presets_list.index - 1)
        await self.auth_presets_list.children[
            self.auth_presets_list.index
        ].remove()

        if self.auth_presets_list.children:
            self.auth_presets_list.index = focus_target_index
            await self._on_select_auth_preset()
        else:
            self._clear_auth_preset()
            self.auth_content_switcher.current = 'auth-empty'

        self.notify('Auth Preset removed', severity='information')

        self.app.request_area.populate_auths()

    @on(Button.Pressed, '#close')
    def _on_close(self) -> None:
        self.dismiss(result=None)

    def _clear_auth_preset(self) -> None:
        self.auth_basic_username_input.value = ''
        self.auth_basic_password_input.value = ''

        self.auth_bearer_token_input.value = ''

        self.auth_api_key_key_input.value = ''
        self.auth_api_key_value_input.value = ''
        self.auth_api_key_where_select.value = 'header'

        self.auth_digest_username_input.value = ''
        self.auth_digest_password_input.value = ''

    async def _populate_auth_presets(self) -> None:
        auth_presets = self.app.auth_presets_repo.get_all().data
        for auth_preset in auth_presets:
            await self._add_auth_preset(
                name=auth_preset.name, id=auth_preset.id
            )

        if auth_presets:
            self.auth_presets_list.index = 0
            await self._on_select_auth_preset()

    async def _add_auth_preset(self, name: str, id: int) -> None:
        await self.auth_presets_list.mount(
            ListItem(Label(name), id=f'auth-preset-{id}')
        )
