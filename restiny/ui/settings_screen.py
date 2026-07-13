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
from restiny.themes import dark_amber, light_amber, system


class SettingsScreen(QWidget):
    def __init__(self, app, settings_repo: SettingsSQLRepo) -> None:
        super().__init__()
        self.app = app
        self.settings_repo = settings_repo

        self.theme_label = QLabel()
        self.theme_label.setText('Theme')
        self.theme_combo_box = QComboBox()
        self.theme_combo_box.addItems(['system', 'dark-amber', 'light-amber'])

        self.save_button = QPushButton()
        self.save_button.setText('Save')

        first_row = QHBoxLayout()
        first_row.addWidget(self.theme_label)
        first_row.addWidget(self.theme_combo_box, 1)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.save_button.clicked.connect(self._on_save)

        self._populate()

    def _populate(self) -> None:
        settings = self.settings_repo.get().data
        self.theme_combo_box.setCurrentText(settings.theme)

    def _on_save(self) -> None:
        if self.theme_combo_box.currentText() == 'system':
            system(self.app)
        elif self.theme_combo_box.currentText() == 'dark-amber':
            dark_amber(self.app)
        elif self.theme_combo_box.currentText() == 'light-amber':
            light_amber(self.app)

        resp = self.settings_repo.set(
            settings=Settings(theme=self.theme_combo_box.currentText())
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to save settings ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
