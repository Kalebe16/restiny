from pathlib import Path
from typing import Literal, Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import Reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static, Switch

from data_fox.utils import filter_paths
from data_fox.widgets import CustomDirectoryTree


class PathChooserScreen(ModalScreen):
    DEFAULT_CSS = """
    PathChooserScreen {
        align: center middle;
    }

    #modal-content {
        border: heavy black;
        background: $surface;
        width: 60%;
        height: 90%;
        layout: grid;
        grid-size: 2 4;
        grid-rows: 1fr 6fr 1fr 1fr;
        padding-left: 1;
        padding-right: 1;
        padding-top: 1;
        grid-gutter: 1;
    }

    #options {
        layout: horizontal;
        column-span: 2;
    }

    CustomDirectoryTree {
        column-span: 2;
        padding-left: 1;
    }

    Input {
        column-span: 2;
    }

    Button {
        width: 100%;
    }

    Label {
        padding-top: 1;
    }
    """

    # TODO: Criar um reactive para o path escolhido
    show_hidden_files: Reactive[bool] = Reactive(False, init=True)
    show_hidden_dirs: Reactive[bool] = Reactive(False, init=True)

    def __init__(
        self, path_type: Literal['file', 'directory'], *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.path_type = path_type

    def compose(self) -> ComposeResult:
        with Container(id='modal-content'):
            with Static(id='options'):
                yield Switch(id='option-show-hidden-files')
                yield Label('Show hidden files?')
                yield Switch(id='option-show-hidden-dirs')
                yield Label('Show hidden directories?')
            yield CustomDirectoryTree(path='/')
            yield Input(
                placeholder='--empty--',
                disabled=True,
                classes='w-full',
                type='text',
            )
            yield Button(label='Cancel', id='cancel')
            yield Button(label='Confirm', id='choose')

    # TODO: Avaliar o uso do `on_ready`
    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content')
        self.switch_show_hidden_files = self.query_one(
            '#option-show-hidden-files'
        )
        self.switch_show_hidden_dirs = self.query_one(
            '#option-show-hidden-dirs'
        )
        self.directory_tree = self.query_one(CustomDirectoryTree)
        self.input = self.query_one(Input)
        self.btn_cancel = self.query_one('#cancel')
        self.btn_confirm = self.query_one('#choose')

        if self.path_type == 'file':
            self.modal_content.border_title = 'File chooser'
        elif self.path_type == 'directory':
            self.modal_content.border_title = 'Directory chooser'

        self.directory_tree.show_root = False
        self.directory_tree.call_after_refresh(
            callback=lambda: self.directory_tree.expand_by_path(
                target_path=Path.home()
            )
        )

    @on(Switch.Changed, '#option-show-hidden-files')
    def on_toggle_hidden_files(self, event: Switch.Changed) -> None:
        self.show_hidden_files = event.value

    @on(Switch.Changed, '#option-show-hidden-dirs')
    def on_toggle_hidden_directories(self, event: Switch.Changed) -> None:
        self.show_hidden_dirs = event.value

    # TODO: Corrigir erro, ao cancelar seleção o input está sendo limpo.
    @on(Button.Pressed, '#cancel')
    def on_cancel(self, event: Button.Pressed) -> None:
        self.dismiss(result=Path(self.input.value))

    @on(Button.Pressed, '#choose')
    def on_confirm(self, event: Button.Pressed) -> None:
        selected_path = Path(self.input.value)
        if not self.input.value:
            self.app.bell()
            self.notify(f'First, choose a {self.path_type}', severity='error')
        elif (self.path_type == 'file' and not selected_path.is_file()) or (
            self.path_type == 'directory' and not selected_path.is_dir()
        ):
            self.app.bell()
            self.notify(f'Choose a valid {self.path_type}', severity='error')
        else:
            self.dismiss(result=Path(self.input.value))

    @on(CustomDirectoryTree.FileSelected)
    def file_select(self, event: CustomDirectoryTree.FileSelected) -> None:
        self.input.value = str(event.path)
        self.input.tooltip = str(event.path)

    @on(CustomDirectoryTree.DirectorySelected)
    def dir_select(self, event: CustomDirectoryTree.DirectorySelected) -> None:
        self.input.value = str(event.path)
        self.input.tooltip = str(event.path)

    async def watch_show_hidden_files(self, value: bool) -> None:
        if value is True:
            self.directory_tree.filter_paths = lambda paths: filter_paths(
                paths=paths,
                show_hidden_files=True,
                show_hidden_dirs=self.show_hidden_dirs,
            )
        elif value is False:
            self.directory_tree.filter_paths = lambda paths: filter_paths(
                paths=paths,
                show_hidden_files=False,
                show_hidden_dirs=self.show_hidden_dirs,
            )

        await self.directory_tree.reload()

    async def watch_show_hidden_dirs(self, value: bool) -> None:
        if value is True:
            self.directory_tree.filter_paths = lambda paths: filter_paths(
                paths=paths,
                show_hidden_files=self.show_hidden_files,
                show_hidden_dirs=True,
            )
        elif value is False:
            self.directory_tree.filter_paths = lambda paths: filter_paths(
                paths=paths,
                show_hidden_files=self.show_hidden_files,
                show_hidden_dirs=False,
            )

        await self.directory_tree.reload()


class PathChooser(Widget):
    DEFAULT_CSS = """
    PathChooser {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 3fr 1fr;
    }
    """

    path: Reactive[Optional[Path]] = Reactive(None, init=True)

    def __init__(
        self, path_type: Literal['file', 'directory'], *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.path_type = path_type

    def compose(self) -> ComposeResult:
        yield Input(placeholder='--empty--', disabled=True, classes='w-full')
        yield Button(f'Choose a {self.path_type}', classes='w-full')

    def on_mount(self) -> None:
        self.input = self.query_one(Input)
        self.button = self.query_one(Button)

    @on(Button.Pressed)
    def open_path_choser(self) -> None:
        def set_path(path: Optional[Path] = None) -> None:
            self.path = path

        self.app.push_screen(
            screen=PathChooserScreen(path_type=self.path_type),
            callback=set_path,
        )

    def watch_path(self, value: Path | None) -> None:
        self.input.value = str(value) if value else ''
        self.input.tooltip = str(value) if value else ''
