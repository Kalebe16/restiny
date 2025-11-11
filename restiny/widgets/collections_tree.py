from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from restiny.enums import HTTPMethod


class CollectionsTree(Tree):
    show_root = False

    def on_mount(self) -> None:
        self.node_by_id: dict[int | None, TreeNode] = {}
        self.node_by_id[None] = self.root
        self.root.data = {'name': '/', 'id': None}

    @property
    def current_parent_folder(self) -> TreeNode:
        if not self.cursor_node:
            return self.root

        return self.cursor_node.parent

    @property
    def current_folder(self) -> TreeNode:
        if not self.cursor_node:
            return self.root

        if self.cursor_node.allow_expand:
            return self.cursor_node
        else:
            return self.cursor_node.parent

    def add_folder(
        self, parent_node: TreeNode | None, name: str, id: int
    ) -> TreeNode:
        parent_node = parent_node or self.root

        node = parent_node.add(label=name)
        node.data = {
            'name': name,
            'id': id,
        }
        self.node_by_id[id] = node
        return node

    def add_request(
        self, parent_node: TreeNode | None, method: str, name: str, id: int
    ) -> TreeNode:
        parent_node = parent_node or self.root

        method_to_color = {
            HTTPMethod.GET: '#00cc66',  # green
            HTTPMethod.POST: '#ffcc00',  # yellow
            HTTPMethod.PUT: '#3388ff',  # blue
            HTTPMethod.PATCH: '#00b3b3',  # teal
            HTTPMethod.DELETE: '#ff3333',  # red
            HTTPMethod.HEAD: '#808080',  # gray
            HTTPMethod.OPTIONS: '#cc66ff',  # magenta
            HTTPMethod.CONNECT: '#ff9966',  # orange
            HTTPMethod.TRACE: '#6666ff',  # violet
        }
        node = parent_node.add_leaf(
            label=f'[{method_to_color[method]}]{method}[/] {name}'
        )
        node.data = {
            'method': method,
            'name': name,
            'id': id,
        }
        self.node_by_id[id] = node
        return node

    def remove(self, node: TreeNode) -> None:
        del self.node_by_id[node.data['id']]
        node.remove()
