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

from restiny.data.repos import RepoStatus
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
class _AddResult:
    kind: Literal['folder', 'request']
    name: str
    parent_id: int | None


@dataclass
class _UpdateResult:
    kind: Literal['folder', 'request']
    name: str
    parent_id: int | None
    old_parent_id: int | None


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

    RadioSet > RadioButton.-selected {
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
        kind: str = 'request',
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


class _AddScreen(_BaseEditScreen):
    @on(Button.Pressed, '#confirm')
    def _on_confirm(self, message: Button.Pressed) -> None:
        kind: str = self.kind_radio_set.pressed_button.label
        name: str = self.name_input.value
        parent_id: int | None = self.parent_select.value

        if not name:
            self.app.notify('Choose a valid name', severity='error')
            return
        if parent_id is None and kind == 'request':
            self.app.notify(
                'Requests can only be created at folders',
                severity='error',
            )
            return

        self.dismiss(
            result=_AddResult(kind=kind, name=name, parent_id=parent_id)
        )


class _UpdateScreen(_BaseEditScreen):
    def on_mount(self) -> None:
        super().on_mount()
        self.kind_radio_set.disabled = True

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self, message: Button.Pressed) -> None:
        kind: str = self.kind_radio_set.pressed_button.label
        name: str = self.name_input.value
        parent_id: int | None = self.parent_select.value
        old_parent_id: str = self._parent_id

        if not name:
            self.app.notify('Choose a valid name', severity='error')
            return
        if parent_id is None and kind == 'request':
            self.app.notify(
                'Requests can only be created at folders',
                severity='error',
            )
            return

        self.dismiss(
            result=_UpdateResult(
                kind=kind,
                name=name,
                parent_id=parent_id,
                old_parent_id=old_parent_id,
            )
        )


class CollectionsArea(Widget):
    if TYPE_CHECKING:
        app: RESTinyApp

    DEFAULT_CSS = """
    CollectionsArea {
        width: 1fr;
        height: 1fr;
        max-width: 15%;
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
        self.content_swiitcher = self.query_one(ContentSwitcher)
        self.colletions_tree = self.query_one(CustomTree)
        self.border_title = 'Collections'

        self._populate_children(node=self.colletions_tree.root)
        self._update_visible_content()

    def prompt_add(self) -> None:
        def _on_prompt_add_result(result: _AddResult | None) -> None:
            if result is None:
                return

            if result.kind == 'request':
                self.add_request(parent_id=result.parent_id, name=result.name)
            elif result.kind == 'folder':
                self.add_folder(parent_id=result.parent_id, name=result.name)

        parents = [
            (parent['path'], parent['id'])
            for parent in self._resolve_all_folder_paths()
        ]
        parent_id = self.colletions_tree.current_expandable_node.data['id']
        self.app.push_screen(
            screen=_AddScreen(parents=parents, parent_id=parent_id),
            callback=_on_prompt_add_result,
        )

    def prompt_update(self) -> None:
        def _on_prompt_update_result(result: _UpdateResult | None) -> None:
            if result is None:
                return

            if result.kind == 'request':
                self.update_request(
                    parent_id=result.parent_id,
                    old_parent_id=result.old_parent_id,
                    name=result.name,
                )
            elif result.kind == 'folder':
                self.update_folder(
                    parent_id=result.parent_id,
                    old_parent_id=result.old_parent_id,
                    name=result.name,
                )

        if not self.colletions_tree.cursor_node:
            return

        node = self.colletions_tree.cursor_node
        name = node.data['name']
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

        parent_id = self.colletions_tree.current_parent_node.data['id']
        self.app.push_screen(
            screen=_UpdateScreen(
                kind=kind, name=name, parents=parents, parent_id=parent_id
            ),
            callback=_on_prompt_update_result,
        )

    def prompt_delete(self) -> None:
        def _on_prompt_delete_result(result: ConfirmPromptResult) -> None:
            if not result.confirmed:
                return

            if self.colletions_tree.cursor_node.allow_expand:
                self.delete_folder()
            else:
                self.delete_request()

        if not self.colletions_tree.cursor_node:
            return

        self.app.push_screen(
            screen=ConfirmPrompt(
                message='Are you sure? This action cannot be undone.'
            ),
            callback=_on_prompt_delete_result,
        )

    def add_folder(self, parent_id: int, name: str) -> None:
        parent_node = self.colletions_tree.node_by_id[parent_id]

        create_resp = self.app.folders_repo.create(
            Folder(name=name, parent_id=parent_id)
        )
        if not create_resp.ok:
            self.notify(message=f'Error: {create_resp.status}', severity='error')
            return

        folder = create_resp.data

        self.notify(
            message="Created successfully!",
            severity="information",
        )

        self._populate_children(parent_node)
        self._update_visible_content()

        self.post_message(message=self.FolderAdded(folder_id=folder.id))

    def add_request(self, parent_id: str, name: str) -> None:
        parent_node = self.colletions_tree.node_by_id[parent_id]

        create_resp = self.app.requests_repo.create(
            Request(folder_id=parent_node.data['id'], name=name)
        )
        if not create_resp.ok:
            self.notify(message=f'Error: {create_resp.status}', severity='error')
            return

        request = create_resp.data

        self.notify(
            message="Created successfully!",
            severity="information",
        )

        self._populate_children(parent_node)
        self._update_visible_content()
        self.post_message(message=self.RequestAdded(request_id=request.id))

    def update_folder(
        self,
        old_parent_id: int | None,
        parent_id: int | None,
        name: str,
    ) -> None:
        old_parent_node = self.colletions_tree.node_by_id[old_parent_id]
        parent_node = self.colletions_tree.node_by_id[parent_id]

        update_resp = self.app.folders_repo.update(
            Folder(
                id=self.colletions_tree.cursor_node.data['id'],
                name=name,
                parent_id=parent_id,
            )
        )
        if not update_resp.ok:
            self.notify(message=f'Error: {update_resp.status}', severity='error')
            return

        self.notify(
            message="Updated successfully!",
            severity="information",
        )

        self._populate_children(old_parent_node)
        self._populate_children(parent_node)
        self._update_visible_content()

        self.post_message(
            message=self.FolderUpdated(
                folder_id=self.colletions_tree.cursor_node.data['id']
            )
        )

    def update_request(
        self, parent_id: int | None, old_parent_id: int | None, name: str
    ) -> None:
        parent_node = self.colletions_tree.node_by_id[parent_id]
        old_parent_node = self.colletions_tree.node_by_id[old_parent_id]

        req: Request = self.app.get_request()
        req.id = self.colletions_tree.cursor_node.data['id']
        req.folder_id = parent_id
        req.name = name
        update_resp = self.app.requests_repo.update(req)
        if not update_resp.ok:
            self.notify(message=f'Error: {update_resp.status}', severity='error')
            return

        self.notify(
            message="Updated successfully!",
            severity="information",
        )

        self._populate_children(parent_node)
        self._populate_children(old_parent_node)
        self._update_visible_content()

        self.post_message(
            message=self.RequestUpdated(
                request_id=self.colletions_tree.cursor_node.data['id']
            )
        )

    def delete_folder(self) -> None:
        self.app.folders_repo.delete_by_id(
            self.colletions_tree.cursor_node.data['id']
        )
        self._populate_children(node=self.colletions_tree.cursor_node.parent)
        self._update_visible_content()
        self.post_message(
            message=self.FolderDeleted(
                folder_id=self.colletions_tree.cursor_node.data['id']
            )
        )

    def delete_request(self) -> None:
        self.app.requests_repo.delete_by_id(
            self.colletions_tree.cursor_node.data['id']
        )
        self._populate_children(node=self.colletions_tree.cursor_node.parent)
        self._update_visible_content()
        self.post_message(
            message=self.RequestDeleted(
                request_id=self.colletions_tree.cursor_node.data['id']
            )
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
                self.colletions_tree.add_leaf_node(
                    parent_node=node, name=item.name, id=item.id
                )
            elif isinstance(item, Folder):
                self.colletions_tree.add_node(
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

    def _update_visible_content(self) -> None:
        if self.colletions_tree.root.children:
            self.content_swiitcher.current = 'content'
        else:
            self.content_swiitcher.current = 'no-content'
