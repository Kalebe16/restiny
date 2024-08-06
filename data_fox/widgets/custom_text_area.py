import pyperclip
from textual.binding import Binding
from textual.events import Key, Paste
from textual.widgets import TextArea

from data_fox.utils import (
    first_char_non_empty,
    next_multiple_of,
    previous_multiple_of,
)


class CustomTextArea(TextArea, inherit_bindings=False):
    BINDINGS = [
        # Cursor movement
        Binding('up', 'cursor_up', 'Cursor up', show=False),
        Binding('down', 'cursor_down', 'Cursor down', show=False),
        Binding('left', 'cursor_left', 'Cursor left', show=False),
        Binding('right', 'cursor_right', 'Cursor right', show=False),
        Binding(
            'ctrl+left', 'cursor_word_left', 'Cursor word left', show=False
        ),
        Binding(
            'ctrl+right', 'cursor_word_right', 'Cursor word right', show=False
        ),
        Binding('home', 'cursor_line_start', 'Cursor line start', show=False),
        Binding('end', 'cursor_line_end', 'Cursor line end', show=False),
        Binding('pageup', 'cursor_page_up', 'Cursor page up', show=False),
        Binding(
            'pagedown', 'cursor_page_down', 'Cursor page down', show=False
        ),
        # Selections
        Binding('shift+up', 'cursor_up(True)', 'Cursor up select', show=False),
        Binding(
            'shift+down', 'cursor_down(True)', 'Cursor down select', show=False
        ),
        Binding(
            'shift+left', 'cursor_left(True)', 'Cursor left select', show=False
        ),
        Binding(
            'shift+right',
            'cursor_right(True)',
            'Cursor right select',
            show=False,
        ),
        Binding(
            'ctrl+shift+left',
            'cursor_word_left(True)',
            'Cursor left word select',
            show=False,
        ),
        Binding(
            'ctrl+shift+right',
            'cursor_word_right(True)',
            'Cursor right word select',
            show=False,
        ),
        Binding(
            'shift+home',
            'cursor_line_start(True)',
            'Cursor line start select',
            show=False,
        ),
        Binding(
            'shift+end',
            'cursor_line_end(True)',
            'Cursor line end select',
            show=False,
        ),
        Binding('ctrl+a', 'select_all', 'Select all', show=False),
        Binding('ctrl+d', 'select_word', 'Select word', show=False),
        Binding('ctrl+l', 'select_line', 'Select line', show=False),
        # Clipboard
        Binding('ctrl+c', 'copy', 'Copy selected', show=False),
        Binding('ctrl+x', 'cut_selected', 'Cut selected', show=False),
        Binding('ctrl+v', 'paste', 'Paste', show=False),
        # Deletion
        Binding(
            'backspace', 'delete_left', 'Delete character left', show=False
        ),
        Binding(
            'delete', 'delete_right', 'Delete character right', show=False
        ),
        Binding(
            'ctrl+backspace',
            'delete_word_left',
            'Delete left to start of word',
            show=False,
        ),
        Binding(
            'ctrl+delete',
            'delete_word_right',
            'Delete right to start of word',
            show=False,
        ),
        Binding(
            'ctrl+shift+u',
            'delete_to_start_of_line',
            'Delete to line start',
            show=False,
        ),
        Binding(
            'ctrl+shift+k',
            'delete_to_end_of_line_or_delete_line',
            'Delete to line end',
            show=False,
        ),
        # Undo/Redo
        Binding('ctrl+z', 'undo', 'Undo', show=False),
        Binding('ctrl+y', 'redo', 'Redo', show=False),
    ]
    """
    | Key(s)                 | Description                                       |
    | :-                     | :-                                                |
    | **Cursor Movement**    |                                                   |
    | up                     | Move the cursor up.                               |
    | down                   | Move the cursor down.                             |
    | left                   | Move the cursor left.                             |
    | right                  | Move the cursor right.                            |
    | ctrl+left              | Move the cursor to the start of the word.         |
    | ctrl+right             | Move the cursor to the end of the word.           |
    | home                   | Move the cursor to the start of the line.         |
    | end                    | Move the cursor to the end of the line.           |
    | pageup                 | Move the cursor one page up.                      |
    | pagedown               | Move the cursor one page down.                    |
    |                        |                                                   |
    | **Selections**         |                                                   |
    | shift+up               | Select while moving the cursor up.                |
    | shift+down             | Select while moving the cursor down.              |
    | shift+left             | Select while moving the cursor left.              |
    | shift+right            | Select while moving the cursor right.             |
    | ctrl+shift+left        | Select to the start of the previous word.         |
    | ctrl+shift+right       | Select to the end of the next word.               |
    | shift+home             | Select from the cursor to the start of the line.  |
    | shift+end              | Select from the cursor to the end of the line.    |
    | ctrl+a                 | Select all text.                                  |
    | ctrl+d                 | Select the current word.                          |
    | ctrl+l                 | Select the current line.                          |
    |                        |                                                   |
    | **Clipboard**          |                                                   |
    | ctrl+c                 | Copy selected text.                               |
    | ctrl+x                 | Cut selected text.                                |
    | ctrl+v                 | Paste clipboard contents.                         |
    |                        |                                                   |
    | **Deletion**           |                                                   |
    | backspace              | Delete character to the left of cursor.           |
    | delete                 | Delete character to the right of cursor.          |
    | ctrl+backspace         | Delete from cursor to start of the word.          |
    | ctrl+delete            | Delete from cursor to end of the word.            |
    | ctrl+shift+u           | Delete from cursor to the start of the line.      |
    | ctrl+shift+k           | Delete from cursor to the end of the line.        |
    |                        |                                                   |
    | **Undo/Redo**          |                                                   |
    | ctrl+z                 | Undo the last action.                             |
    | ctrl+y                 | Redo the last undone action.                      |
    |                        |                                                   |
    | **Indentation**        |                                                   |
    | tab                    | Add indentation                                   |
    | shift+tab              | Remove indentation                                |
    """

    def action_copy(self) -> None:
        selection_start, selection_end = self.selection
        selected_text = self.get_text_range(
            start=selection_start, end=selection_end
        )

        if selected_text.strip() == '':
            # Copy current line
            cursor_line, _ = self.cursor_location
            line_content = self.document.get_line(cursor_line)
            pyperclip.copy(text=line_content)
        else:
            # Copy selected text
            pyperclip.copy(text=self.selected_text)

    def action_cut_selected(self) -> None:
        if self.read_only:
            return

        selection_start, selection_end = self.selection
        selected_text = self.get_text_range(
            start=selection_start, end=selection_end
        )

        if selected_text.strip() == '':
            # Cut current line
            cursor_line, _ = self.cursor_location
            line_content = self.document.get_line(cursor_line)
            pyperclip.copy(text=line_content)
            self.action_delete_line()
            self.action_delete_left()
        else:
            # Cut selected text
            pyperclip.copy(text=self.selected_text)
            self.delete(start=self.selection.start, end=self.selection.end)

    async def action_paste(self) -> None:
        """
        Hack to make the Ctrl+V shortcut behave the same way as Ctrl+Shift+V.

        In terminal-based or Textual interfaces, the paste event is usually tied to
        the Ctrl+Shift+V shortcut. This method forces the behavior for Ctrl+V by
        manually creating a Paste event using the clipboard's content and passing
        it to the base `_on_paste` handler.
        """
        if self.read_only:
            return
        await super()._on_paste(event=Paste(text=pyperclip.paste()))

    # TODO: Refactor this.
    async def action_insert_tab(self) -> None:
        """
        Add tab (indentation) to current line or to all selected lines.
        """
        if self.read_only:
            return

        selection_start, selection_end = self.selection
        selected_text = self.get_text_range(
            start=selection_start, end=selection_end
        )

        if selected_text.strip() == '':
            # Single line, add tab to current line
            current_line, current_column = self.cursor_location
            next_tab_column = next_multiple_of(
                multiple_of=self.indent_width, current_number=current_column
            )
            spaces_to_add = next_tab_column - current_column
            self.insert(' ' * spaces_to_add)
        else:
            # Multiple lines, add tab to all selected lines
            lines = self.selected_text.splitlines()
            indented_lines = []
            for line_content in lines:
                current_column = (
                    first_char_non_empty(text=line_content)
                    if line_content.strip() != ''
                    else 0
                )
                next_tab_column = next_multiple_of(
                    multiple_of=self.indent_width,
                    current_number=current_column,
                )
                spaces_to_add = next_tab_column - current_column
                indented_lines.append((' ' * spaces_to_add) + line_content)

            indented_text = '\n'.join(indented_lines)
            self.replace(indented_text, selection_start, selection_end)

    # TODO: Refactor this.
    async def action_remove_tab(self) -> None:
        """
        Remove tab (indentation) from current line or selection.
        """
        if self.read_only:
            return

        selection_start, selection_end = self.selection
        selected_text = self.get_text_range(
            start=selection_start, end=selection_end
        )

        if selected_text.strip() == '':
            # Single line, remove tab from current line
            current_line, current_column = self.cursor_location
            line_content = self.document.get_line(current_line)
            current_column = (
                first_char_non_empty(text=line_content)
                if line_content.strip() != ''
                else 0
            )
            previous_tab_column = previous_multiple_of(
                current_number=current_column, multiple_of=self.indent_width
            )
            spaces_to_remove = current_column - previous_tab_column
            if spaces_to_remove > 0 and current_column > 0:
                start = (current_line, 0)
                end = (current_line, spaces_to_remove)
                self.delete(start, end)
        else:
            # Multiple lines: remove tab from all selected lines
            lines = selected_text.splitlines()
            detabbed_lines = [
                line[self.indent_width :]
                if line.startswith(' ' * self.indent_width)
                else line
                for line in lines
            ]
            self.replace(
                '\n'.join(detabbed_lines), selection_start, selection_end
            )

    async def on_key(self, event: Key) -> None:
        BRACKETS_MAP = {
            '(': '()',
            '[': '[]',
            '{': '{}',
            "'": "''",
            '"': '""',
        }
        brackets_pair = BRACKETS_MAP.get(event.character)
        if brackets_pair:
            self.insert(brackets_pair)
            self.move_cursor_relative(columns=-1)
            event.prevent_default()
            event.stop()

        if event.key == 'tab':
            await self.action_insert_tab()
            event.prevent_default()
            event.stop()
        elif event.key == 'shift+tab':
            await self.action_remove_tab()
            event.prevent_default()
            event.stop()
