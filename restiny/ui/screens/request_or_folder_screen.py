from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    RadioButton,
    RadioSet,
    Select,
)

from restiny.entities import Folder, Request
from restiny.widgets import (
    CustomInput,
)

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


@dataclass
class AddFolderResult:
    id: int
    parent_id: int | None
    name: str


@dataclass
class AddRequestResult:
    id: int
    folder_id: int
    name: str


@dataclass
class UpdateFolderResult:
    id: int
    parent_id: int | None
    old_parent_id: int | None
    name: str


@dataclass
class UpdateRequestResult:
    id: int
    folder_id: int
    old_folder_id: int
    name: str


class _BaseEditRequestOrFolderScreen(ModalScreen):
    DEFAULT_CSS = """
    _BaseEditRequestOrFolderScreen {
        align: center middle;
    }

    #modal-content {
        border: heavy black;
        border-title-color: gray;
        background: $surface;
        width: auto;
        height: auto;
        max-width: 40%
    }

    _BaseEditRequestOrFolderScreen RadioSet > RadioButton.-selected {
        background: $surface;
    }
    """
    AUTO_FOCUS = '#name'

    BINDINGS = [
        Binding(
            key='escape',
            action='dismiss',
            description='Quit the screen',
            show=False,
        ),
    ]

    def __init__(
        self,
        kind: Literal['request', 'folder'] = 'request',
        name: str = '',
        parents: list[tuple[str, int | None]] = [],
        parent_id: int | None = None,
    ) -> None:
        super().__init__()
        self._kind = kind
        self._name = name
        self._parents = parents
        self._parent_id = parent_id

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-content'):
            with Horizontal(classes='w-auto h-auto mt-1'):
                with RadioSet(id='kind', classes='w-auto', compact=True):
                    yield RadioButton(
                        'request',
                        value=self._kind == 'request',
                        classes='w-auto',
                    )
                    yield RadioButton(
                        'folder',
                        value=self._kind == 'folder',
                        classes='w-auto',
                    )
            with Horizontal(classes='w-auto h-auto mt-1'):
                yield CustomInput(
                    value=self._name,
                    placeholder='Title',
                    select_on_focus=False,
                    classes='w-1fr',
                    id='name',
                )
            with Horizontal(classes='w-auto h-auto mt-1'):
                yield Select(
                    self._parents,
                    value=self._parent_id,
                    tooltip='Parent',
                    allow_blank=False,
                    id='parent',
                )
            with Horizontal(classes='w-auto h-auto mt-1'):
                yield Button(label='Cancel', classes='w-1fr', id='cancel')
                yield Button(label='Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)
        self.kind_radio_set = self.query_one('#kind', RadioSet)
        self.name_input = self.query_one('#name', CustomInput)
        self.parent_select = self.query_one('#parent', Select)
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Create request/folder'

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self, message: Button.Pressed) -> None:
        self.dismiss(result=None)

    def _common_validation(self) -> bool:
        kind: str = self.kind_radio_set.pressed_button.label
        name: str = self.name_input.value
        parent_id: int | None = self.parent_select.value

        if not name:
            self.app.notify('Name is required', severity='error')
            return False
        if parent_id is None and kind == 'request':
            self.app.notify(
                'Requests must belong to a folder',
                severity='error',
            )
            return False

        return True


class AddRequestOrFolderScreen(_BaseEditRequestOrFolderScreen):
    app: 'RESTinyApp'

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self, message: Button.Pressed) -> None:
        if not self._common_validation():
            return

        kind: str = self.kind_radio_set.pressed_button.label
        name: str = self.name_input.value
        parent_id: int | None = self.parent_select.value

        if kind == 'folder':
            resp = self.app.folders_repo.create(
                Folder(name=name, parent_id=parent_id)
            )
            if not resp.ok:
                self.app.notify(
                    f'Failed to create folder ({resp.status})',
                    severity='error',
                )
                return
            self.app.notify('Folder created', severity='information')
            self.dismiss(
                result=AddFolderResult(
                    id=resp.data.id,
                    parent_id=parent_id,
                    name=name,
                )
            )

        elif kind == 'request':
            resp = self.app.requests_repo.create(
                Request(name=name, folder_id=parent_id)
            )
            if not resp.ok:
                self.app.notify(
                    f'Failed to create request ({resp.status})',
                    severity='error',
                )
                return
            self.app.notify('Request created', severity='information')
            self.dismiss(
                result=AddRequestResult(
                    id=resp.data.id, folder_id=parent_id, name=name
                )
            )


class UpdateRequestOrFolderScreen(_BaseEditRequestOrFolderScreen):
    app: 'RESTinyApp'

    def __init__(self, id: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._id = id

    def on_mount(self) -> None:
        super().on_mount()
        self.kind_radio_set.disabled = True

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self, message: Button.Pressed) -> None:
        if not self._common_validation():
            return

        kind: str = self.kind_radio_set.pressed_button.label
        name: str = self.name_input.value
        parent_id: int | None = self.parent_select.value
        old_parent_id: int | None = self._parent_id

        if kind == 'folder':
            folder = self.app.folders_repo.get_by_id(id=self._id).data
            folder.name = name
            folder.parent_id = parent_id
            resp = self.app.folders_repo.update(folder=folder)
            if not resp.ok:
                self.app.notify(
                    f'Failed to update folder ({resp.status})',
                    severity='error',
                )
                return
            self.app.notify('Folder updated', severity='information')
            self.dismiss(
                result=UpdateFolderResult(
                    id=resp.data.id,
                    parent_id=parent_id,
                    old_parent_id=old_parent_id,
                    name=name,
                )
            )
        elif kind == 'request':
            request = self.app.requests_repo.get_by_id(id=self._id).data
            request.name = name
            request.folder_id = parent_id
            update_resp = self.app.requests_repo.update(request)
            if not update_resp.ok:
                self.app.notify(
                    f'Failed to update request ({update_resp.status})',
                    severity='error',
                )
                return
            self.app.notify('Request updated', severity='information')
            self.dismiss(
                result=UpdateRequestResult(
                    id=update_resp.data.id,
                    folder_id=parent_id,
                    old_folder_id=old_parent_id,
                    name=name,
                )
            )
