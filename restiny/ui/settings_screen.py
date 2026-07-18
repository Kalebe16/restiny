from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from restiny.data.repos import (
    SettingsSQLRepo,
)
from restiny.entities import Settings
from restiny.themes import dark, light
from restiny.widgets.color_picker import ColorPicker


class SettingsScreen(QWidget):
    def __init__(self, app, settings_repo: SettingsSQLRepo) -> None:
        super().__init__()
        self.app = app
        self.settings_repo = settings_repo

        self.theme_label = QLabel('Theme')
        self.theme_combo_box = QComboBox()
        self.theme_combo_box.addItems(['dark', 'light'])

        self.accent_color_label = QLabel('Accent color')
        self.accent_color_picker = ColorPicker()

        self.save_button = QPushButton('Save')

        first_row = QHBoxLayout()
        first_row.addWidget(self.theme_label)
        first_row.addWidget(self.theme_combo_box, 1)

        second_row = QHBoxLayout()
        second_row.addWidget(self.accent_color_label)
        second_row.addWidget(self.accent_color_picker)

        third_row = QHBoxLayout()
        third_row.addStretch()
        third_row.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addLayout(second_row)
        layout.addStretch()
        layout.addLayout(third_row)

        self.save_button.clicked.connect(self._on_save)

        self._populate()

    def _populate(self) -> None:
        settings = self.settings_repo.get().data
        self.theme_combo_box.setCurrentText(settings.theme)
        self.accent_color_picker.set_color(settings.accent_color)

    def _on_save(self) -> None:
        accent_color = self.accent_color_picker.get_color()
        if self.theme_combo_box.currentText() == 'dark':
            dark(accent_color=accent_color)
        elif self.theme_combo_box.currentText() == 'light':
            light(accent_color=accent_color)

        resp = self.settings_repo.set(
            settings=Settings(
                theme=self.theme_combo_box.currentText(),
                accent_color=accent_color,
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to save settings ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
