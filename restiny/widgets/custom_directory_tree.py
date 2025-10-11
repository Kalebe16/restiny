import asyncio
from pathlib import Path

from textual.widgets import DirectoryTree
from textual.widgets._tree import TreeNode


class CustomDirectoryTree(DirectoryTree):
    async def expand_by_path(self, target_path: Path) -> None:
        """
        Expands the directory tree to reveal the target path.
        """

        async def expand_to_target_path_recursively(
            current_node: TreeNode, target_path: Path
        ) -> None:
            for child_node in current_node.children:
                child_path = child_node.data.path  # Current directory path

                if (
                    target_path.is_relative_to(child_path)
                    or child_path == target_path
                ):
                    child_node.expand()
                    await asyncio.sleep(
                        0.1
                    )  # Hack to wait for children to populate
                    self.move_cursor(node=child_node)
                    await expand_to_target_path_recursively(
                        current_node=child_node, target_path=target_path
                    )
                    return

        # Start expanding from the root of the directory tree
        await expand_to_target_path_recursively(self.root, target_path)
