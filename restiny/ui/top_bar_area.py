from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from restiny.data.repos import (
    EnvironmentsSQLRepo,
    FoldersSQLRepo,
    RequestsSQLRepo,
)


class TopBarArea(QWidget):
    sig_folder_tab_selected = Signal(int)
    sig_folder_tab_closed = Signal(int)
    sig_request_tab_selected = Signal(int)
    sig_request_tab_closed = Signal(int)
    sig_all_tabs_closed = Signal()

    def __init__(
        self,
        environments_repo: EnvironmentsSQLRepo,
        requests_repo: RequestsSQLRepo,
        folders_repo: FoldersSQLRepo,
    ) -> None:
        super().__init__()
        self.environments_repo = environments_repo
        self.requests_repo = requests_repo
        self.folders_repo = folders_repo

        self.opened_tabs = QTabBar()
        self.opened_tabs.setMovable(True)
        self.opened_tabs.setTabsClosable(True)
        self.path_label = QLabel()
        self.path_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
                font-style: italic;
                padding: 2px 4px;
            }
        """)
        self.environment_combo_box = QComboBox()

        first_row = QHBoxLayout()
        first_row.addWidget(self.opened_tabs)
        first_row.addStretch()
        first_row.addWidget(self.environment_combo_box)

        second_row = QHBoxLayout()
        second_row.addWidget(self.path_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(first_row)
        layout.addLayout(second_row)

        self.opened_tabs.tabCloseRequested.connect(self._on_close_tab)
        self.opened_tabs.currentChanged.connect(self._on_select_tab)

        self._populate_environments()

    def get_data(self) -> dict:
        environment_name = None
        if self.environment_combo_box.currentText() != 'No environment':
            environment_name = self.environment_combo_box.currentText()
        return {
            'environment': environment_name,
            'path': self.path_label.text(),
        }

    def open_folder_tab(self, folder_id: int, folder_name: str) -> None:
        for tab_index in range(self.opened_tabs.count()):
            tab_data = self.opened_tabs.tabData(tab_index)
            if tab_data['type'] == 'folder' and tab_data['id'] == folder_id:
                self.opened_tabs.setCurrentIndex(tab_index)
                self.opened_tabs.show()
                self.path_label.setText(
                    _resolve_folder_path(
                        folders_repo=self.folders_repo, folder_id=folder_id
                    )
                )
                return

        index = self.opened_tabs.addTab(folder_name)
        self.opened_tabs.setTabData(index, {'type': 'folder', 'id': folder_id})
        self.opened_tabs.setCurrentIndex(index)
        self.opened_tabs.show()
        self.path_label.setText(
            _resolve_folder_path(
                folders_repo=self.folders_repo, folder_id=folder_id
            )
        )

    def open_request_tab(self, request_id: int, request_name: str) -> None:
        for tab_index in range(self.opened_tabs.count()):
            tab_data = self.opened_tabs.tabData(tab_index)
            if tab_data['type'] == 'request' and tab_data['id'] == request_id:
                self.opened_tabs.setCurrentIndex(tab_index)
                self.opened_tabs.show()
                self.path_label.setText(
                    _resolve_request_path(
                        requests_repo=self.requests_repo,
                        folders_repo=self.folders_repo,
                        request_id=request_id,
                    )
                )
                return

        index = self.opened_tabs.addTab(request_name)
        self.opened_tabs.setTabData(
            index, {'type': 'request', 'id': request_id}
        )
        self.opened_tabs.setCurrentIndex(index)
        self.opened_tabs.show()
        self.path_label.setText(
            _resolve_request_path(
                requests_repo=self.requests_repo,
                folders_repo=self.folders_repo,
                request_id=request_id,
            )
        )

    def mark_request_unsaved_tab(self, request_id: int) -> None:
        for tab_index in range(self.opened_tabs.count()):
            tab_data = self.opened_tabs.tabData(tab_index)

            if tab_data['type'] == 'request' and tab_data['id'] == request_id:
                text = self.opened_tabs.tabText(tab_index).replace('*', '')
                self.opened_tabs.setTabText(tab_index, text + '*')
                return

    def mark_request_saved_tab(self, request_id: int) -> None:
        for tab_index in range(self.opened_tabs.count()):
            tab_data = self.opened_tabs.tabData(tab_index)

            if tab_data['type'] == 'request' and tab_data['id'] == request_id:
                text = self.opened_tabs.tabText(tab_index).replace('*', '')
                self.opened_tabs.setTabText(tab_index, text)
                return

    def mark_folder_unsaved_tab(self, folder_id: int) -> None:
        for tab_index in range(self.opened_tabs.count()):
            tab_data = self.opened_tabs.tabData(tab_index)

            if tab_data['type'] == 'folder' and tab_data['id'] == folder_id:
                text = self.opened_tabs.tabText(tab_index).replace('*', '')
                self.opened_tabs.setTabText(tab_index, text + '*')
                return

    def mark_folder_saved_tab(self, folder_id: int) -> None:
        for tab_index in range(self.opened_tabs.count()):
            tab_data = self.opened_tabs.tabData(tab_index)

            if tab_data['type'] == 'folder' and tab_data['id'] == folder_id:
                text = self.opened_tabs.tabText(tab_index).replace('*', '')
                self.opened_tabs.setTabText(tab_index, text)
                return

    def update_tabs(self) -> None:
        for tab_index in reversed(range(self.opened_tabs.count())):
            tab_data = self.opened_tabs.tabData(tab_index)

            if tab_data['type'] == 'request':
                request_id = tab_data['id']

                request = self.requests_repo.get_by_id(id=request_id).data
                if not request:
                    self._on_close_tab(tab_index)
                    continue

                tab_text = f'{request.method} {request.name}'
                if self.opened_tabs.tabText(tab_index).endswith('*'):
                    self.opened_tabs.setTabText(tab_index, tab_text + '*')
                else:
                    self.opened_tabs.setTabText(tab_index, tab_text)
            elif tab_data['type'] == 'folder':
                folder_id = tab_data['id']

                folder = self.folders_repo.get_by_id(id=folder_id).data
                if not folder:
                    self._on_close_tab(tab_index)
                    continue

                tab_text = folder.name
                if self.opened_tabs.tabText(tab_index).endswith('*'):
                    self.opened_tabs.setTabText(tab_index, tab_text + '*')
                else:
                    self.opened_tabs.setTabText(tab_index, tab_text)

        current_index = self.opened_tabs.currentIndex()
        if current_index >= 0:
            tab_data = self.opened_tabs.tabData(current_index)
            if tab_data['type'] == 'request':
                self.path_label.setText(
                    _resolve_request_path(
                        requests_repo=self.requests_repo,
                        folders_repo=self.folders_repo,
                        request_id=tab_data['id'],
                    )
                )
            elif tab_data['type'] == 'folder':
                self.path_label.setText(
                    _resolve_folder_path(
                        folders_repo=self.folders_repo,
                        folder_id=tab_data['id'],
                    )
                )

    def _on_close_tab(self, tab_index: int) -> None:
        if tab_index >= 0:
            tab_data = self.opened_tabs.tabData(tab_index)
            if tab_data['type'] == 'request':
                request_id = tab_data['id']
                self.opened_tabs.removeTab(tab_index)
                self.sig_request_tab_closed.emit(request_id)
            elif tab_data['type'] == 'folder':
                folder_id = tab_data['id']
                self.opened_tabs.removeTab(tab_index)
                self.sig_folder_tab_closed.emit(folder_id)

            if self.opened_tabs.count() == 0:
                self.path_label.setText('')
                self.sig_all_tabs_closed.emit()

    def _on_select_tab(self, tab_index: int) -> None:
        if tab_index >= 0:
            tab_data = self.opened_tabs.tabData(tab_index)
            if not tab_data:
                return

            if tab_data['type'] == 'request':
                request_id = tab_data['id']
                self.sig_request_tab_selected.emit(request_id)
            elif tab_data['type'] == 'folder':
                folder_id = tab_data['id']
                self.sig_folder_tab_selected.emit(folder_id)

    def _populate_environments(self) -> None:
        environments = self.environments_repo.get_all().data
        self.environment_combo_box.clear()
        self.environment_combo_box.addItem('No environment')
        for environment in environments:
            if environment.name == 'global':
                continue
            self.environment_combo_box.addItem(environment.name)


def _resolve_folder_path(
    folders_repo: FoldersSQLRepo,
    folder_id: int,
) -> str:
    parts: list[str] = []
    current = folders_repo.get_by_id(folder_id).data
    while current:
        parts.insert(0, current.name)
        if current.parent_id is None:
            break
        current = folders_repo.get_by_id(current.parent_id).data
    return '/' + '/'.join(parts)


def _resolve_request_path(
    folders_repo: FoldersSQLRepo,
    requests_repo: RequestsSQLRepo,
    request_id: int,
) -> str:
    request = requests_repo.get_by_id(request_id).data
    if not request:
        return '/'

    if request.folder_id is None:
        return f'/{request.method} {request.name}'

    folder_path = _resolve_folder_path(folders_repo, request.folder_id)
    return f'{folder_path}/{request.method} {request.name}'
