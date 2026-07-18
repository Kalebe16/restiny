from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from restiny.enums import HTTPMethod


class URLArea(QWidget):
    sig_send_requested = Signal()
    sig_download_requested = Signal()
    sig_cancel_requested = Signal()
    sig_edited = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._request_pending = False

        self.method_combo_box = QComboBox()
        self.method_combo_box.addItems([method for method in HTTPMethod])

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('Enter URL')

        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.hide()

        self.send_button = QPushButton('Send')

        self.download_button = QPushButton('Download')

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.method_combo_box)
        controls_layout.addWidget(self.url_input)
        controls_layout.addWidget(self.cancel_button)
        controls_layout.addWidget(self.send_button)
        controls_layout.addWidget(self.download_button)

        self.group_box = QGroupBox('URL')
        self.group_box.setLayout(controls_layout)

        layout = QVBoxLayout(self)
        layout.addWidget(self.group_box)

        self.method_combo_box.currentTextChanged.connect(
            lambda: self.sig_edited.emit()
        )
        self.url_input.textChanged.connect(lambda: self.sig_edited.emit())
        self.url_input.returnPressed.connect(self._on_send)
        self.send_button.clicked.connect(self._on_send)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.download_button.clicked.connect(self._on_download)

    @property
    def request_pending(self) -> bool:
        return self._request_pending

    @request_pending.setter
    def request_pending(self, value: bool) -> None:
        if value is True:
            self.send_button.hide()
            self.download_button.hide()
            self.cancel_button.show()
        elif value is False:
            self.send_button.show()
            self.download_button.show()
            self.cancel_button.hide()
        self._request_pending = value

    def clear_data(self) -> None:
        self.method_combo_box.setCurrentText(HTTPMethod.GET)
        self.url_input.clear()

    def get_data(self) -> dict:
        return dict(
            method=HTTPMethod(self.method_combo_box.currentText()),
            url=self.url_input.text(),
        )

    def set_data(self, data: dict) -> None:
        self.method_combo_box.setCurrentText(data['method'])
        self.url_input.setText(data['url'])

    def _on_send(self) -> None:
        if self.request_pending:
            return

        self.sig_send_requested.emit()

    def _on_download(self) -> None:
        if self.request_pending:
            return

        self.sig_download_requested.emit()

    def _on_cancel(self) -> None:
        if not self.request_pending:
            return

        self.sig_cancel_requested.emit()
