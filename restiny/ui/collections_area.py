from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    Button,
    ContentSwitcher,
    RadioButton,
    RadioSet,
    Select,
    Static,
)

from restiny.entities import Folder, Request
from restiny.widgets import (
    ConfirmPrompt,
    ConfirmPromptResult,
    CustomInput,
    CustomTree,
)

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


@dataclass
class _AddFolderResult:
    id: int
    parent_id: int | None
    name: str


@dataclass
class _AddRequestResult:
    id: int
    folder_id: int
    name: str


@dataclass
class _UpdateFolderResult:
    id: int
    parent_id: int | None
    old_parent_id: int | None
    name: str


@dataclass
class _UpdateRequestResult:
    id: int
    folder_id: int
    old_folder_id: int
    name: str


class _BaseEditScreen(ModalScreen):
    DEFAULT_CSS = """
    _BaseEditScreen {
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

    _BaseEditScreen RadioSet > RadioButton.-selected {
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


class _AddScreen(_BaseEditScreen):
    if TYPE_CHECKING:
        app: RESTinyApp

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
                result=_AddFolderResult(
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
                result=_AddRequestResult(
                    id=resp.data.id, folder_id=parent_id, name=name
                )
            )


class _UpdateScreen(_BaseEditScreen):
    if TYPE_CHECKING:
        app: RESTinyApp

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
                result=_UpdateFolderResult(
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
                result=_UpdateRequestResult(
                    id=update_resp.data.id,
                    folder_id=parent_id,
                    old_folder_id=old_parent_id,
                    name=name,
                )
            )


class CollectionsArea(Widget):
    if TYPE_CHECKING:
        app: RESTinyApp

    ALLOW_MAXIMIZE = True
    focusable = True
    DEFAULT_CSS = """
    CollectionsArea {
        width: 1fr;
        height: 1fr;
        border: heavy black;
        border-title-color: gray;
    }

    Static {
        padding: 1;
    }
    """

    class RequestAdded(Message):
        def __init__(self, request_id: int) -> None:
            super().__init__()
            self.request_id = request_id

    class RequestUpdated(Message):
        def __init__(self, request_id: int) -> None:
            super().__init__()
            self.request_id = request_id

    class RequestDeleted(Message):
        def __init__(self, request_id: int) -> None:
            super().__init__()
            self.request_id = request_id

    class RequestSelected(Message):
        def __init__(self, request_id: int) -> None:
            super().__init__()
            self.request_id = request_id

    class FolderAdded(Message):
        def __init__(self, folder_id: int) -> None:
            super().__init__()
            self.folder_id = folder_id

    class FolderUpdated(Message):
        def __init__(self, folder_id: int) -> None:
            super().__init__()
            self.folder_id = folder_id

    class FolderDeleted(Message):
        def __init__(self, folder_id: int) -> None:
            super().__init__()
            self.folder_id = folder_id

    class FolderSelected(Message):
        def __init__(self, folder_id: int) -> None:
            super().__init__()
            self.folder_id = folder_id

    def compose(self) -> ComposeResult:
        with ContentSwitcher(id='switcher', initial='no-content'):
            yield Static(
                "[i]No collections yet. Press [b]'ctrl+n'[/] to create your first one.[/]",
                id='no-content',
            )
            yield CustomTree('Collections', id='content')

    def on_mount(self) -> None:
        self.content_switcher = self.query_one(ContentSwitcher)
        self.collections_tree = self.query_one(CustomTree)
        self.border_title = 'Collections'

        self._populate_children(node=self.collections_tree.root)
        self._sync_content_switcher()

    def prompt_add(self) -> None:
        parents = [
            (parent['path'], parent['id'])
            for parent in self._resolve_all_folder_paths()
        ]
        parent_id = self.collections_tree.current_expandable_node.data['id']
        self.app.push_screen(
            screen=_AddScreen(parents=parents, parent_id=parent_id),
            callback=self._on_prompt_add_result,
        )

    def prompt_update(self) -> None:
        if not self.collections_tree.cursor_node:
            return

        node = self.collections_tree.cursor_node
        kind = None
        parents = []
        if node.allow_expand:
            kind = 'folder'
            parents = [
                (parent['path'], parent['id'])
                for parent in self._resolve_all_folder_paths()
                if parent['id'] != node.data['id']
            ]
        else:
            kind = 'request'
            parents = [
                (parent['path'], parent['id'])
                for parent in self._resolve_all_folder_paths()
            ]

        parent_id = self.collections_tree.current_parent_node.data['id']
        self.app.push_screen(
            screen=_UpdateScreen(
                kind=kind,
                name=node.data['name'],
                parents=parents,
                parent_id=parent_id,
                id=node.data['id'],
            ),
            callback=self._on_prompt_update_result,
        )

    def prompt_delete(self) -> None:
        if not self.collections_tree.cursor_node:
            return

        self.app.push_screen(
            screen=ConfirmPrompt(
                message='Are you sure? This action cannot be undone.'
            ),
            callback=self._on_prompt_delete_result,
        )

    @on(CustomTree.NodeExpanded)
    def _on_node_expanded(self, message: CustomTree.NodeExpanded) -> None:
        self._populate_children(node=message.node)

    @on(CustomTree.NodeSelected)
    def _on_node_selected(self, message: CustomTree.NodeSelected) -> None:
        if message.node.allow_expand:
            self.post_message(
                message=self.FolderSelected(folder_id=message.node.data['id'])
            )
        else:
            self.post_message(
                message=self.RequestSelected(
                    request_id=message.node.data['id']
                )
            )

    def _on_prompt_add_result(
        self, result: _AddFolderResult | _AddRequestResult | None
    ) -> None:
        if result is None:
            return

        if isinstance(result, _AddRequestResult):
            parent_node = self.collections_tree.node_by_id[result.folder_id]
            self._populate_children(parent_node)
            self._sync_content_switcher()
            self.post_message(message=self.RequestAdded(request_id=result.id))
        elif isinstance(result, _AddFolderResult):
            parent_node = self.collections_tree.node_by_id[result.parent_id]
            self._populate_children(parent_node)
            self._sync_content_switcher()
            self.post_message(message=self.FolderAdded(folder_id=result.id))

    def _on_prompt_update_result(
        self, result: _UpdateFolderResult | _UpdateRequestResult | None
    ) -> None:
        if result is None:
            return

        if isinstance(result, _UpdateRequestResult):
            parent_node = self.collections_tree.node_by_id[result.folder_id]
            old_parent_node = self.collections_tree.node_by_id[
                result.old_folder_id
            ]
            self._populate_children(parent_node)
            self._populate_children(old_parent_node)
            self._sync_content_switcher()
            self.post_message(
                message=self.RequestUpdated(request_id=result.id)
            )
        elif isinstance(result, _UpdateFolderResult):
            parent_node = self.collections_tree.node_by_id[result.parent_id]
            old_parent_node = self.collections_tree.node_by_id[
                result.old_parent_id
            ]
            self._populate_children(parent_node)
            self._populate_children(old_parent_node)
            self._sync_content_switcher()
            self.post_message(message=self.FolderUpdated(folder_id=result.id))

    def _on_prompt_delete_result(self, result: ConfirmPromptResult) -> None:
        if not result.confirmed:
            return

        if self.collections_tree.cursor_node.allow_expand:
            self.app.folders_repo.delete_by_id(
                self.collections_tree.cursor_node.data['id']
            )
            self.notify('Folder deleted', severity='information')
            self._populate_children(
                node=self.collections_tree.cursor_node.parent
            )
            self._sync_content_switcher()
            self.post_message(
                message=self.FolderDeleted(
                    folder_id=self.collections_tree.cursor_node.data['id']
                )
            )
        else:
            self.app.requests_repo.delete_by_id(
                self.collections_tree.cursor_node.data['id']
            )
            self.notify('Request deleted', severity='information')
            self._populate_children(
                node=self.collections_tree.cursor_node.parent
            )
            self._sync_content_switcher()
            self.post_message(
                message=self.RequestDeleted(
                    request_id=self.collections_tree.cursor_node.data['id']
                )
            )

    def _populate_children(self, node) -> None:
        folder_id = node.data['id']

        for child in list(node.children):
            child.remove()

        folders = self.app.folders_repo.list_by_parent_id(folder_id).data
        requests = self.app.requests_repo.list_by_folder_id(folder_id).data

        for item in sorted(
            folders + requests, key=lambda item: item.name.lower()
        ):
            if isinstance(item, Request):
                self.collections_tree.add_leaf_node(
                    parent_node=node, name=item.name, id=item.id
                )
            elif isinstance(item, Folder):
                self.collections_tree.add_node(
                    parent_node=node, name=item.name, id=item.id
                )

    def _resolve_all_folder_paths(self) -> list[dict[str, str | int | None]]:
        paths: list[dict[str, str | int | None]] = [{'path': '/', 'id': None}]

        paths_stack: list[tuple[str, int | None]] = [('/', None)]
        while paths_stack:
            parent_path, parent_id = paths_stack.pop(0)

            if parent_id is None:
                children = self.app.folders_repo.list_roots().data
            else:
                children = self.app.folders_repo.list_by_parent_id(
                    parent_id
                ).data

            for folder in children:
                path = f'{parent_path.rstrip("/")}/{folder.name}'
                paths.append({'path': path, 'id': folder.id})
                paths_stack.append((path, folder.id))

        return paths

    def _sync_content_switcher(self) -> None:
        if self.collections_tree.root.children:
            self.content_switcher.current = 'content'
        else:
            self.content_switcher.current = 'no-content'
