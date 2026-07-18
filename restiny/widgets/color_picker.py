from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class ColorPicker(QWidget):
    def __init__(self):
        super().__init__()

        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText('Escolha uma cor...')
        self.color_input.setDisabled(True)

        self.pick_button = QPushButton('Pick Color')
        self.pick_button.clicked.connect(self._open_color_dialog)

        layout = QHBoxLayout(self)
        layout.addWidget(self.color_input, 1)
        layout.addWidget(self.pick_button)

    def _open_color_dialog(self):
        color = QColorDialog.getColor(QColor(), self, 'Select Color')
        if color.isValid():
            self.color_input.setText(color.name())

    def get_color(self) -> str:
        return self.color_input.text()

    def set_color(self, color: str) -> None:
        self.color_input.setText(color)
