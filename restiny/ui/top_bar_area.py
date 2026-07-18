from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QTabBar,
    QWidget,
)

from restiny.data.repos import (
    EnvironmentsSQLRepo,
    RequestsSQLRepo,
)


class TopBarArea(QWidget):
    sig_tab_selected = Signal(int)
    sig_tab_closed = Signal(int)
    sig_all_tabs_closed = Signal()

    def __init__(
        self,
        environments_repo: EnvironmentsSQLRepo,
        requests_repo: RequestsSQLRepo,
    ) -> None:
        super().__init__()
        self.environments_repo = environments_repo
        self.requests_repo = requests_repo

        self.opened_requests_tabs = QTabBar()
        self.opened_requests_tabs.setMovable(True)
        self.opened_requests_tabs.setTabsClosable(True)
        self.environment_combo_box = QComboBox()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(
            self.opened_requests_tabs, 0, Qt.AlignmentFlag.AlignLeft
        )
        layout.addStretch()
        layout.addWidget(
            self.environment_combo_box, 0, Qt.AlignmentFlag.AlignRight
        )

        self.opened_requests_tabs.tabCloseRequested.connect(self._on_close_tab)
        self.opened_requests_tabs.currentChanged.connect(self._on_select_tab)

        self._populate_environments()

    def get_data(self) -> dict:
        environment_name = None
        if self.environment_combo_box.currentText() != 'No environment':
            environment_name = self.environment_combo_box.currentText()
        return {'environment_name': environment_name}

    def open_request_tab(self, request_id: int, request_name: str) -> None:
        for i in range(self.opened_requests_tabs.count()):
            if self.opened_requests_tabs.tabData(i) == request_id:
                self.opened_requests_tabs.setCurrentIndex(i)
                self.opened_requests_tabs.show()
                return

        index = self.opened_requests_tabs.addTab(request_name)
        self.opened_requests_tabs.setTabData(index, request_id)
        self.opened_requests_tabs.setCurrentIndex(index)
        self.opened_requests_tabs.show()

    def mark_unsaved_tab(self, request_id: int) -> None:
        for i in range(self.opened_requests_tabs.count()):
            if self.opened_requests_tabs.tabData(i) == request_id:
                text = self.opened_requests_tabs.tabText(i).replace('*', '')
                self.opened_requests_tabs.setTabText(i, text + '*')

    def mark_saved_tab(self, request_id: int) -> None:
        for i in range(self.opened_requests_tabs.count()):
            if self.opened_requests_tabs.tabData(i) == request_id:
                text = self.opened_requests_tabs.tabText(i).replace('*', '')
                self.opened_requests_tabs.setTabText(i, text)

    def update_tabs(self) -> None:
        for i in reversed(range(self.opened_requests_tabs.count())):
            request_id = self.opened_requests_tabs.tabData(i)
            if request_id is None:
                continue

            request = self.requests_repo.get_by_id(id=request_id).data
            if not request:
                self._on_close_tab(i)
                continue

            tab_text = f'{request.method} {request.name}'
            if self.opened_requests_tabs.tabText(i).endswith('*'):
                self.opened_requests_tabs.setTabText(i, tab_text + '*')
            else:
                self.opened_requests_tabs.setTabText(i, tab_text)

    def _on_close_tab(self, tab_index: int) -> None:
        if tab_index >= 0:
            request_id = self.opened_requests_tabs.tabData(tab_index)
            self.opened_requests_tabs.removeTab(tab_index)
            self.sig_tab_closed.emit(request_id)
            if self.opened_requests_tabs.count() == 0:
                self.sig_all_tabs_closed.emit()

    def _on_select_tab(self, tab_index: int) -> None:
        if tab_index >= 0:
            request_id = self.opened_requests_tabs.tabData(tab_index)
            if request_id is not None:
                self.sig_tab_selected.emit(request_id)

    def _populate_environments(self) -> None:
        environments = self.environments_repo.get_all().data
        self.environment_combo_box.clear()
        self.environment_combo_box.addItem('No environment')
        for environment in environments:
            if environment.name == 'global':
                continue
            self.environment_combo_box.addItem(environment.name)
