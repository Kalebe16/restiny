from textual.widgets import Tree
from textual.widgets.tree import TreeNode


class CustomTree(Tree):
    show_root = False

    def on_mount(self) -> None:
        self.node_by_id: dict[int | None, TreeNode] = {}
        self.node_by_id[None] = self.root
        self.root.data = {'path': '/', 'name': '/', 'id': None}

    @property
    def current_parent_node(self) -> TreeNode:
        if not self.cursor_node:
            return self.root

        return self.cursor_node.parent

    @property
    def current_expandable_node(self) -> TreeNode:
        if not self.cursor_node:
            return self.root

        if self.cursor_node.allow_expand:
            return self.cursor_node
        else:
            return self.cursor_node.parent

    def add_node(
        self, parent_node: TreeNode | None, name: str, id: int
    ) -> TreeNode:
        parent_node = parent_node or self.root

        node = parent_node.add(name)
        node.data = {
            'name': name,
            'id': id,
        }
        self.node_by_id[id] = node
        return node

    def add_leaf_node(
        self, parent_node: TreeNode | None, name: str, id: int
    ) -> TreeNode:
        parent_node = parent_node or self.root

        node = parent_node.add_leaf(name)
        node.data = {
            'name': name,
            'id': id,
        }
        self.node_by_id[id] = node
        return node
