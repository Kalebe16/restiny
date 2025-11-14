from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Rule

from restiny.entities import Environment
from restiny.widgets import DynamicFields, TextDynamicField
from restiny.widgets.custom_input import CustomInput

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class EnvironmentsScreen(ModalScreen):
    app: 'RESTinyApp'

    DEFAULT_CSS = """
    EnvironmentsScreen {
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
    AUTO_FOCUS = '#environments-list'

    BINDINGS = [
        Binding(
            key='escape',
            action='dismiss',
            description='Quit the screen',
            show=False,
        ),
    ]

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-content'):
            with Horizontal(classes='w-auto p-1'):
                with Vertical(classes='w-1fr h-auto'):
                    yield ListView(
                        classes='',
                        id='environments-list',
                    )
                    with Horizontal(classes='w-auto h-auto mt-1'):
                        yield CustomInput(
                            placeholder='Environment name',
                            classes='w-4fr',
                            id='environment-name',
                        )
                        yield Button(
                            label='➕',
                            tooltip='Add environment',
                            classes='',
                            id='add-environment',
                        )

                yield Rule(orientation='vertical')

                with Vertical(classes='w-2fr h-auto'):
                    with Horizontal(classes='w-auto h-auto'):
                        yield CustomInput(
                            placeholder='Environment name',
                            classes='w-5fr',
                            id='environment-rename',
                        )
                        yield Button(
                            '💾',
                            tooltip='Save environment',
                            classes='w-1fr',
                            id='save-environment',
                        )
                        yield Button(
                            '➖',
                            tooltip='Delete environment',
                            classes='w-1fr',
                            id='delete-environment',
                        )
                    yield DynamicFields(
                        fields=[
                            TextDynamicField(enabled=False, key='', value='')
                        ],
                        classes='mt-1',
                        id='variables',
                    )
                    yield Label(
                        "[i]Tip: You can use [b]'{{var}}'[/] or [b]'${var}'[/] in requests to reference variables.[/]",
                        classes='mt-1',
                    )
            with Horizontal(classes='w-auto h-auto'):
                yield Button(label='Close', classes='w-1fr', id='close')

    async def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)
        self.environments_list = self.query_one('#environments-list', ListView)
        self.environment_name_input = self.query_one(
            '#environment-name', CustomInput
        )
        self.add_environment_button = self.query_one(
            '#add-environment', Button
        )
        self.environment_rename_input = self.query_one(
            '#environment-rename', CustomInput
        )
        self.save_environment_button = self.query_one(
            '#save-environment', Button
        )
        self.delete_environment_button = self.query_one(
            '#delete-environment', Button
        )
        self.variables_dynamic_fields = self.query_one(
            '#variables', DynamicFields
        )
        self.close_button = self.query_one('#close', Button)

        self.modal_content.border_title = 'Environments'

        await self._populate_environments()

    @property
    def _selected_env_id(self) -> int | None:
        if self.environments_list.index is None:
            return None

        return int(
            self.environments_list.children[
                self.environments_list.index
            ].id.rsplit('-', 1)[1]
        )

    @property
    def _selected_env_name(self) -> str | None:
        if self.environments_list.index is None:
            return None

        return (
            self.environments_list.children[self.environments_list.index]
            .children[0]
            .content
        )

    @on(ListView.Selected, '#environments-list')
    async def _on_select_environment(self) -> None:
        self.environment_rename_input.value = self._selected_env_name
        is_global = self._selected_env_name == 'global'
        self.environment_rename_input.disabled = is_global
        self.delete_environment_button.disabled = is_global

        for field in self.variables_dynamic_fields.fields:
            self.variables_dynamic_fields.remove_field(field=field)

        environment = self.app.environments_repo.get_by_id(
            self._selected_env_id
        ).data
        for variable in environment.variables:
            await self.variables_dynamic_fields.add_field(
                field=TextDynamicField(
                    enabled=variable.enabled,
                    key=variable.key,
                    value=variable.value,
                ),
                before_last=True,
            )

    @on(Button.Pressed, '#add-environment')
    @on(CustomInput.Submitted, '#environment-name')
    async def _on_add_environment(self) -> None:
        if not self.environment_name_input.value.strip():
            self.notify('Environment name is required', severity='error')
            return

        create_resp = self.app.environments_repo.create(
            Environment(name=self.environment_name_input.value, variables=[])
        )
        if not create_resp.ok:
            self.notify(
                f'Failed to create environment ({create_resp.status})',
                severity='error',
            )
            return

        await self._add_environment(
            name=create_resp.data.name, id=create_resp.data.id
        )
        self.environment_name_input.value = ''
        self.environments_list.index = len(self.environments_list.children) - 1
        await self._on_select_environment()
        self.notify('Environment added', severity='information')

    @on(Button.Pressed, '#save-environment')
    @on(CustomInput.Submitted, '#environment-rename')
    async def _on_save_environment(self) -> None:
        if not self.environment_rename_input.value.strip():
            self.notify('Environment name is required', severity='error')
            return

        update_resp = self.app.environments_repo.update(
            Environment(
                id=self._selected_env_id,
                name=self.environment_rename_input.value,
                variables=[
                    Environment.Variable(
                        enabled=variable.enabled,
                        key=variable.key,
                        value=variable.value,
                    )
                    for variable in self.variables_dynamic_fields.filled_fields
                ],
            )
        )
        if not update_resp.ok:
            self.notify(
                f'Failed to update environment ({update_resp.status})',
                severity='error',
            )
            return

        self.environments_list.children[self.environments_list.index].children[
            0
        ].update(update_resp.data.name)
        self.notify('Environment updated', severity='information')

    @on(Button.Pressed, '#delete-environment')
    async def _on_remove_environment(self) -> None:
        if self.environments_list.index is None:
            self.notify('No environment selected', severity='error')
            return

        self.app.environments_repo.delete_by_id(self._selected_env_id)
        focus_target_index = max(0, self.environments_list.index - 1)
        await self.environments_list.children[
            self.environments_list.index
        ].remove()
        self.environments_list.index = focus_target_index
        await self._on_select_environment()
        self.notify('Environment removed', severity='information')

    @on(Button.Pressed, '#close')
    async def _on_close(self, message: Button.Pressed) -> None:
        self.dismiss(result=None)

    async def _populate_environments(self) -> None:
        environments = self.app.environments_repo.get_all().data
        for environment in environments:
            await self._add_environment(
                name=environment.name, id=environment.id
            )

        self.environments_list.index = 0
        await self._on_select_environment()

    async def _add_environment(self, name: str, id: int) -> None:
        await self.environments_list.mount(
            ListItem(Label(name), id=f'env-{id}')
        )
