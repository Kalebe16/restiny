from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from restiny.data.repos import (
    EnvironmentsSQLRepo,
    SettingsSQLRepo,
)
from restiny.entities import Environment
from restiny.utils import fix_pyside_stylesheet
from restiny.widgets.dynamic_fields import DynamicFields, TextDynamicField


class EnvironmentScreen(QWidget):
    sig_removed = Signal()
    sig_added = Signal()
    sig_saved = Signal()

    def __init__(
        self,
        main_window: QMainWindow,
        environments_repo: EnvironmentsSQLRepo,
        settings_repo: SettingsSQLRepo,
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.environments_repo = environments_repo
        self.settings_repo = settings_repo
        self.selected_environment: Environment | None = None

        self.add_environment_button = QPushButton('Add')
        self.environments_list = QListWidget()
        self._populate_environments()

        left_col = QVBoxLayout()
        left_col.addWidget(self.add_environment_button)
        left_col.addWidget(self.environments_list)

        self.environment_name_input = QLineEdit()
        self.variables_dynamic_fields = DynamicFields(
            fields=[TextDynamicField()]
        )
        self.tip_label = QLabel()
        self.tip_label.setText(
            "Tip: You can use '{{var}}' or '${var}' to reference variables."
        )
        self.tip_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.remove_environment_button = QPushButton('Remove')
        self.save_environment_button = QPushButton('Save')

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        bottom_row.addWidget(self.tip_label)
        bottom_row.addStretch()
        bottom_row.addWidget(self.remove_environment_button)
        bottom_row.addWidget(self.save_environment_button)

        self.right_col = QVBoxLayout()
        self.right_col.addWidget(self.environment_name_input)
        self.right_col.addWidget(self.variables_dynamic_fields)
        self.right_col.addLayout(bottom_row)

        layout = QHBoxLayout(self)
        layout.addLayout(left_col, 1)
        layout.addLayout(self.right_col, 4)

        self.variables_dynamic_fields.sig_edited.connect(
            lambda: fix_pyside_stylesheet(
                window=self.main_window,
                accent_color=self.settings_repo.get().data.accent_color,
            )
        )
        self.remove_environment_button.clicked.connect(
            self._on_remove_environment
        )
        self.add_environment_button.clicked.connect(self._on_add_environment)
        self.environments_list.clicked.connect(self._on_select_environment)
        self.save_environment_button.clicked.connect(self._on_save_environment)

        environments_list_items = self.environments_list.findItems(
            'global', Qt.MatchExactly
        )
        if environments_list_items:
            self.environments_list.setCurrentItem(environments_list_items[0])
            index = self.environments_list.indexFromItem(
                environments_list_items[0]
            )
            self._on_select_environment(index)

    def _populate_environments(self) -> None:
        environments = self.environments_repo.get_all().data
        self.environments_list.clear()
        for env in environments:
            self.environments_list.addItem(env.name)

    def _on_select_environment(self, index) -> None:
        env_name = self.environments_list.item(index.row()).text()

        self.environment_name_input.setText(env_name)

        if env_name == 'global':
            self.environment_name_input.setDisabled(True)
            self.remove_environment_button.setDisabled(True)
        else:
            self.environment_name_input.setDisabled(False)
            self.remove_environment_button.setDisabled(False)

        for field in self.variables_dynamic_fields.fields:
            self.variables_dynamic_fields.remove_field(field)

        for env in self.environments_repo.get_all().data:
            if env.name != env_name:
                continue

            for var in env.variables:
                self.variables_dynamic_fields.add_field(
                    TextDynamicField(
                        enabled=var.enabled, key=var.key, value=var.value
                    )
                )

        self.environment_name_input.setFocus()
        self.selected_environment = self.environments_repo.get_by_name(
            name=env_name
        ).data

    def _on_add_environment(self) -> None:
        dialog = AddEnvironmentDialog(
            parent=self, environments_repo=self.environments_repo
        )
        dialog.sig_added.connect(self._populate_environments)
        dialog.exec()

        new_name = dialog.name_input.text()
        environments_list_items = self.environments_list.findItems(
            new_name, Qt.MatchExactly
        )
        if environments_list_items:
            self.environments_list.setCurrentItem(environments_list_items[0])
            index = self.environments_list.indexFromItem(
                environments_list_items[0]
            )
            self._on_select_environment(index)

        self.sig_added.emit()

    def _on_save_environment(self) -> None:
        variables = []
        for data in self.variables_dynamic_fields.get_data():
            variables.append(
                Environment.Variable(
                    enabled=data['enabled'],
                    key=data['key'],
                    value=data['value'],
                )
            )
        resp = self.environments_repo.update(
            environment=self.selected_environment.model_copy(
                update={
                    'name': self.environment_name_input.text(),
                    'variables': variables,
                }
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to save environment ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText('Environment saved')
        msg.setWindowTitle('Information')
        msg.exec()
        self._populate_environments()

        self.sig_saved.emit()

    def _on_remove_environment(self) -> None:
        dialog = RemoveEnvironmentDialog(
            parent=self,
            environemnts_repo=self.environments_repo,
            environment_name=self.selected_environment.name,
        )
        dialog.sig_removed.connect(self._populate_environments)
        dialog.exec()

        environments_list_items = self.environments_list.findItems(
            'global', Qt.MatchExactly
        )
        if environments_list_items:
            self.environments_list.setCurrentItem(environments_list_items[0])
            index = self.environments_list.indexFromItem(
                environments_list_items[0]
            )
            self._on_select_environment(index)

        self.sig_removed.emit()


class RemoveEnvironmentDialog(QDialog):
    sig_removed = Signal()

    def __init__(
        self,
        parent: QWidget,
        environemnts_repo: EnvironmentsSQLRepo,
        environment_name: str,
    ) -> None:
        super().__init__(parent)
        self.environemnts_repo = environemnts_repo
        self.environment_name = environment_name
        self.environment = self.environemnts_repo.get_by_name(
            name=self.environment_name
        ).data

        self.setWindowTitle('Remove request')
        self.resize(400, 100)

        self.are_you_sure_label = QLabel()
        self.are_you_sure_label.setText('Are you sure?')
        self.are_you_sure_label.setAlignment(Qt.AlignCenter)

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.are_you_sure_label)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        resp = self.environemnts_repo.delete_by_id(id=self.environment.id)
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to delete environment ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        self.sig_removed.emit()
        self.accept()


class AddEnvironmentDialog(QDialog):
    sig_added = Signal()

    def __init__(
        self, parent: QWidget, environments_repo: EnvironmentsSQLRepo
    ):
        super().__init__(parent)
        self.environments_repo = environments_repo

        self.setWindowTitle('Add Environment')
        self.resize(400, 100)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('Name')

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.name_input)

        second_row = QHBoxLayout()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

        # Fix focus
        for button in (
            self.cancel_button,
            self.confirm_button,
        ):
            button.setAutoDefault(False)
            button.setDefault(False)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        if self.name_input.text() == 'No environment':
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Failed to create environment (reserved name)')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        resp = self.environments_repo.create(
            environment=Environment(
                name=self.name_input.text(),
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to create environment ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        self.sig_added.emit()
        self.accept()
