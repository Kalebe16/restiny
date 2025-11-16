from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    ContentSwitcher,
    Static,
)
from textual.widgets.tree import TreeNode

from restiny.entities import Request
from restiny.enums import HTTPMethod
from restiny.ui.screens.request_or_folder_screen import (
    AddFolderResult,
    AddRequestOrFolderScreen,
    AddRequestResult,
    UpdateFolderResult,
    UpdateRequestOrFolderScreen,
    UpdateRequestResult,
)
from restiny.widgets import (
    CollectionsTree,
    ConfirmPrompt,
)

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class CollectionsArea(Widget):
    app: 'RESTinyApp'

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
            yield CollectionsTree('Collections', id='content')

    def on_mount(self) -> None:
        self.content_switcher = self.query_one(ContentSwitcher)
        self.collections_tree = self.query_one(CollectionsTree)
        self.border_title = 'Collections'

        self.populate_children(node=self.collections_tree.root)
        self._sync_content_switcher()

    def prompt_add(self) -> None:
        parents = [
            (parent['path'], parent['id'])
            for parent in self._resolve_all_folder_paths()
        ]
        parent_id = self.collections_tree.current_folder.data['id']
        self.app.push_screen(
            screen=AddRequestOrFolderScreen(
                parents=parents, parent_id=parent_id
            ),
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

        parent_id = self.collections_tree.current_parent_folder.data['id']
        self.app.push_screen(
            screen=UpdateRequestOrFolderScreen(
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

    def populate_children(self, node: TreeNode) -> None:
        folder_id = node.data['id']

        folders = self.app.folders_repo.get_by_parent_id(folder_id).data
        requests = self.app.requests_repo.get_by_folder_id(folder_id).data

        def sort_requests(request: Request) -> tuple:
            methods = [method.value for method in HTTPMethod]
            method_order = {
                method: index for index, method in enumerate(methods)
            }
            return (method_order[request.method], request.name.lower())

        sorted_folders = sorted(
            folders, key=lambda folder: folder.name.lower()
        )
        sorted_requests = sorted(requests, key=sort_requests)

        for child_node in list(node.children):
            self.collections_tree.remove(child_node)

        for folder in sorted_folders:
            self.collections_tree.add_folder(
                parent_node=node, name=folder.name, id=folder.id
            )

        for request in sorted_requests:
            self.collections_tree.add_request(
                parent_node=node,
                method=request.method,
                name=request.name,
                id=request.id,
            )

        node.refresh()
        self._sync_content_switcher()

    @on(CollectionsTree.NodeExpanded)
    def _on_node_expanded(self, message: CollectionsTree.NodeExpanded) -> None:
        self.populate_children(node=message.node)

    @on(CollectionsTree.NodeSelected)
    def _on_node_selected(self, message: CollectionsTree.NodeSelected) -> None:
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
        self, result: AddFolderResult | AddRequestResult | None
    ) -> None:
        if result is None:
            return

        if isinstance(result, AddRequestResult):
            parent_node = self.collections_tree.node_by_id[result.folder_id]
            self.populate_children(parent_node)
            self._sync_content_switcher()
            self.post_message(message=self.RequestAdded(request_id=result.id))
        elif isinstance(result, AddFolderResult):
            parent_node = self.collections_tree.node_by_id[result.parent_id]
            self.populate_children(parent_node)
            self._sync_content_switcher()
            self.post_message(message=self.FolderAdded(folder_id=result.id))

    def _on_prompt_update_result(
        self, result: UpdateFolderResult | UpdateRequestResult | None
    ) -> None:
        if result is None:
            return

        if isinstance(result, UpdateRequestResult):
            parent_node = self.collections_tree.node_by_id[result.folder_id]
            old_parent_node = self.collections_tree.node_by_id[
                result.old_folder_id
            ]
            self.populate_children(parent_node)
            self.populate_children(old_parent_node)
            self._sync_content_switcher()
            self.post_message(
                message=self.RequestUpdated(request_id=result.id)
            )
        elif isinstance(result, UpdateFolderResult):
            parent_node = self.collections_tree.node_by_id[result.parent_id]
            old_parent_node = self.collections_tree.node_by_id[
                result.old_parent_id
            ]
            self.populate_children(parent_node)
            self.populate_children(old_parent_node)
            self._sync_content_switcher()
            self.post_message(message=self.FolderUpdated(folder_id=result.id))

    def _on_prompt_delete_result(self, result: bool) -> None:
        if result is False:
            return

        try:
            prev_selected_index_in_parent = (
                self.collections_tree.cursor_node.parent.children.index(
                    self.collections_tree.cursor_node
                )
            )
        except ValueError:
            prev_selected_index_in_parent = 0

        if self.collections_tree.cursor_node.allow_expand:
            self.app.folders_repo.delete_by_id(
                self.collections_tree.cursor_node.data['id']
            )
            self.notify('Folder deleted', severity='information')
            self.populate_children(
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
            self.populate_children(
                node=self.collections_tree.cursor_node.parent
            )
            self._sync_content_switcher()
            self.post_message(
                message=self.RequestDeleted(
                    request_id=self.collections_tree.cursor_node.data['id']
                )
            )

        if self.collections_tree.cursor_node.parent.children:
            next_index_to_select = min(
                prev_selected_index_in_parent,
                len(self.collections_tree.cursor_node.parent.children) - 1,
            )
            next_node_to_select = (
                self.collections_tree.cursor_node.parent.children[
                    next_index_to_select
                ]
            )
        else:
            next_node_to_select = self.collections_tree.cursor_node.parent
        self.call_after_refresh(
            lambda: self.collections_tree.select_node(next_node_to_select)
        )

    def _resolve_all_folder_paths(self) -> list[dict[str, str | int | None]]:
        paths: list[dict[str, str | int | None]] = [{'path': '/', 'id': None}]

        paths_stack: list[tuple[str, int | None]] = [('/', None)]
        while paths_stack:
            parent_path, parent_id = paths_stack.pop(0)

            if parent_id is None:
                children = self.app.folders_repo.get_roots().data
            else:
                children = self.app.folders_repo.get_by_parent_id(
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
