from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class PasswordInput(QWidget):
    sig_edited = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.toggle_button = QPushButton('show')
        self.toggle_button.setCheckable(True)
        self.toggle_button.setFixedWidth(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.password_input, 1)
        layout.addWidget(self.toggle_button)

        self.toggle_button.toggled.connect(self._on_toggle)
        self.password_input.textChanged.connect(lambda: self.sig_edited.emit())

    def _on_toggle(self, checked: bool) -> None:
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_button.setText('hide')
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_button.setText('show')

    def text(self) -> str:
        return self.password_input.text()

    def setText(self, value: str) -> None:
        self.password_input.setText(value)

    def setPlaceholderText(self, value: str) -> None:
        self.password_input.setPlaceholderText(value)
