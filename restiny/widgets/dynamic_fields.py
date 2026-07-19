from pathlib import Path
from typing import Literal

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class TextDynamicField(QWidget):
    sig_enabled = Signal()
    sig_disabled = Signal()
    sig_empty = Signal()
    sig_filled = Signal()
    sig_remove_requested = Signal()
    sig_edited = Signal()

    def __init__(self, enabled: bool = False, key: str = '', value: str = ''):
        super().__init__()
        self.initial_enabled = enabled
        self.initial_key = key
        self.initial_value = value

        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.toggled.connect(self._on_enabled_or_disabled)
        self.enable_checkbox.setToolTip('Enable')
        self.enable_checkbox.setStyleSheet("""
QCheckBox::indicator {
    width: 20px;
    height: 20px;
}
""")
        self.enable_checkbox.setChecked(self.initial_enabled)
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText('Key')
        self.key_input.textEdited.connect(self._on_edited)
        self.key_input.setText(self.initial_key)
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText('Value')
        self.value_input.textEdited.connect(self._on_edited)
        self.value_input.setText(self.initial_value)
        self.remove_button = QPushButton()
        self.remove_button.setText('Remove')
        self.remove_button.setFocusPolicy(Qt.TabFocus | Qt.ClickFocus)
        self.remove_button.clicked.connect(self._on_remove_requested)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.addWidget(self.enable_checkbox)
        layout.addWidget(self.key_input)
        layout.addWidget(self.value_input)
        layout.addWidget(self.remove_button)

        self.enable_checkbox.toggled.connect(lambda: self.sig_edited.emit())
        self.key_input.textEdited.connect(lambda: self.sig_edited.emit())
        self.value_input.textEdited.connect(lambda: self.sig_edited.emit())

    @property
    def is_filled(self) -> bool:
        return self.key_input.text() or self.value_input.text()

    @property
    def is_empty(self) -> bool:
        return not self.is_filled

    def get_data(self) -> dict:
        return dict(
            enabled=self.enable_checkbox.isChecked(),
            key=self.key_input.text(),
            value=self.value_input.text(),
        )

    def clear_data(self) -> None:
        self.enable_checkbox.setChecked(False)
        self.key_input.setText('')
        self.value_input.setText('')

    def _on_enabled_or_disabled(self, checked: bool) -> None:
        if checked:
            self.sig_enabled.emit()
        else:
            self.sig_disabled.emit()

    def _on_edited(self) -> None:
        if self.is_empty:
            self.sig_empty.emit()
        else:
            self.sig_filled.emit()

    def _on_remove_requested(self) -> None:
        self.sig_remove_requested.emit()


class TextOrFileDynamicField(QWidget):
    sig_enabled = Signal()
    sig_disabled = Signal()
    sig_empty = Signal()
    sig_filled = Signal()
    sig_remove_requested = Signal()
    sig_edited = Signal()

    def __init__(
        self,
        enabled: bool = False,
        key: str = '',
        value: str | Path | None = '',
        value_kind: Literal['text', 'file'] = 'text',
    ):
        super().__init__()
        self.initial_enabled = enabled
        self.initial_key = key
        self.initial_value = value
        self.initial_value_kind = value_kind

        self.text_radio = QRadioButton('Text')
        self.file_radio = QRadioButton('File')
        self.text_radio.setChecked(True)
        self.text_radio.toggled.connect(self._on_text_kind_selected)
        self.file_radio.toggled.connect(self._on_file_kind_selected)

        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(self.initial_enabled)
        self.enable_checkbox.setToolTip('Enable')
        self.enable_checkbox.setStyleSheet("""
QCheckBox::indicator {
    width: 20px;
    height: 20px;
}
""")
        self.enable_checkbox.toggled.connect(self._on_enabled_or_disabled)

        self.key_input = QLineEdit(self.initial_key)
        self.key_input.setPlaceholderText('Key')
        self.key_input.textEdited.connect(self._on_edited)

        self.value_input = QLineEdit(self.initial_value)
        self.value_input.setPlaceholderText('Value')
        self.value_input.textEdited.connect(self._on_edited)

        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)

        self.file_button = QPushButton('Browse')
        self.file_button.clicked.connect(self._on_select_file)

        file_widget = QWidget()
        file_layout = QHBoxLayout(file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.file_button)

        self.value_stack = QStackedWidget()
        self.value_stack.addWidget(self.value_input)
        self.value_stack.addWidget(file_widget)
        self.value_stack.setFixedHeight(self.value_input.sizeHint().height())

        self.remove_button = QPushButton('Remove')
        self.remove_button.setFocusPolicy(Qt.ClickFocus)
        self.remove_button.clicked.connect(self._on_remove_requested)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.addWidget(self.text_radio)
        layout.addWidget(self.file_radio)
        layout.addWidget(self.enable_checkbox)
        layout.addWidget(self.key_input)
        layout.addWidget(self.value_stack)
        layout.addWidget(self.remove_button)

        self.file_radio.toggled.connect(lambda: self.sig_edited.emit())
        self.text_radio.toggled.connect(lambda: self.sig_edited.emit())
        self.enable_checkbox.toggled.connect(lambda: self.sig_edited.emit())
        self.key_input.textEdited.connect(lambda: self.sig_edited.emit())
        self.value_input.textEdited.connect(lambda: self.sig_edited.emit())
        self.file_input.textEdited.connect(lambda: self.sig_edited.emit())

    @property
    def is_filled(self) -> bool:
        if self.key_input.text():
            return True
        elif self.text_radio.isChecked() and self.value_input.text():
            return True
        elif self.file_radio.isChecked() and self.file_input.text():
            return True
        else:
            return False

    @property
    def is_empty(self) -> bool:
        return not self.is_filled

    def get_data(self) -> dict:
        if self.file_radio.isChecked():
            value_kind = 'file'
            value = self.file_input.text()
        elif self.text_radio.isChecked():
            value_kind = 'text'
            value = self.value_input.text()

        return dict(
            enabled=self.enable_checkbox.isChecked(),
            key=self.key_input.text(),
            value=value,
            value_kind=value_kind,
        )

    def clear_data(self) -> None:
        self.text_radio.setChecked(True)
        self.file_radio.setChecked(False)
        self.enable_checkbox.setChecked(False)
        self.key_input.setText('')
        self.value_input.setText('')
        self.file_input.setText('')

    def _on_enabled_or_disabled(self, checked: bool) -> None:
        if checked:
            self.sig_enabled.emit()
        else:
            self.sig_disabled.emit()

    def _on_edited(self) -> None:
        if self.is_empty:
            self.sig_empty.emit()
        else:
            self.sig_filled.emit()

    def _on_remove_requested(self) -> None:
        self.sig_remove_requested.emit()

    def _on_text_kind_selected(self, checked: bool) -> None:
        if not checked:
            return

        self.value_stack.setCurrentIndex(0)

    def _on_file_kind_selected(self, checked: bool) -> None:
        if not checked:
            return

        self.value_stack.setCurrentIndex(1)

    def _on_select_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, 'Select file')

        if not filename:
            return

        self.file_input.setText(filename)
        self._on_edited()


class DynamicFields(QWidget):
    sig_edited = Signal()

    def __init__(
        self,
        fields: list[TextDynamicField | TextOrFileDynamicField],
    ) -> None:
        super().__init__()

        self.initial_fields = fields

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        inner = QWidget()

        self.layout = QVBoxLayout(inner)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(inner)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)

        field_type = type(fields[0])

        for field in fields:
            self.add_field(field)

        if not self.fields or self.fields[-1].is_filled:
            self.add_field(field_type())

    @property
    def fields(self) -> list[TextDynamicField | TextOrFileDynamicField]:
        return [
            self.layout.itemAt(index).widget()
            for index in range(self.layout.count())
        ]

    def add_field(
        self,
        field: TextDynamicField | TextOrFileDynamicField,
    ) -> None:
        field.sig_empty.connect(lambda: self.remove_field(field))
        field.sig_filled.connect(self.ensure_empty_field)
        field.sig_filled.connect(
            lambda: field.enable_checkbox.setChecked(True)
        )
        field.sig_remove_requested.connect(lambda: self.remove_field(field))
        field.sig_edited.connect(lambda: self.sig_edited.emit())
        if self.fields and self.fields[-1].is_empty:
            self.layout.insertWidget(self.layout.count() - 1, field)
        else:
            self.layout.addWidget(field)
        QTimer.singleShot(0, self._update_tab_order)

    def ensure_empty_field(self) -> None:
        field_type = type(self.fields[0])
        if all(field.is_filled for field in self.fields):
            field = field_type()
            field.sig_edited.connect(lambda: self.sig_edited.emit())
            self.add_field(field)

    def remove_field(
        self,
        field: TextDynamicField | TextOrFileDynamicField,
    ) -> None:
        if field is self.fields[-1]:
            return

        to_focus = 'key_input'
        if field.key_input.hasFocus():
            to_focus = 'key_input'
        elif field.value_input.hasFocus():
            to_focus = 'value_input'
        elif hasattr(field, 'file_input') and field.file_input.hasFocus():
            to_focus = 'file_input'
        elif hasattr(field, 'file_button') and field.file_button.hasFocus():
            to_focus = 'file_button'

        if field is self.fields[-2]:
            if to_focus == 'key_input':
                self.fields[-1].key_input.setFocus()
            elif to_focus == 'value_input':
                self.fields[-1].value_input.setFocus()
            elif to_focus == 'file_input':
                self.fields[-1].file_input.setFocus()
            elif to_focus == 'file_button':
                self.fields[-1].file_button.setFocus()
        else:
            if to_focus == 'key_input':
                self.fields[self.fields.index(field) + 1].key_input.setFocus()
            elif to_focus == 'value_input':
                self.fields[
                    self.fields.index(field) + 1
                ].value_input.setFocus()
            elif to_focus == 'file_input':
                self.fields[self.fields.index(field) + 1].file_input.setFocus()
            elif to_focus == 'file_button':
                self.fields[
                    self.fields.index(field) + 1
                ].file_button.setFocus()

        self.layout.removeWidget(field)
        field.deleteLater()
        self.sig_edited.emit()

    def clear_data(self):
        for field in self.fields:
            field.clear_data()
            self.remove_field(field)

    def get_data(self) -> list[dict]:
        return [field.get_data() for field in self.fields if field.is_filled]

    # TODO: Refactor
    def _update_tab_order(self) -> None:
        fields = self.fields

        for index, field in enumerate(fields):
            is_text_or_file = isinstance(field, TextOrFileDynamicField)

            if is_text_or_file:
                QWidget.setTabOrder(field.text_radio, field.file_radio)
                QWidget.setTabOrder(field.file_radio, field.enable_checkbox)

            QWidget.setTabOrder(field.enable_checkbox, field.key_input)

            if is_text_or_file:
                if field.text_radio.isChecked():
                    QWidget.setTabOrder(field.key_input, field.value_input)
                    QWidget.setTabOrder(field.value_input, field.remove_button)
                else:
                    QWidget.setTabOrder(field.key_input, field.file_input)
                    QWidget.setTabOrder(field.file_input, field.file_button)
                    QWidget.setTabOrder(field.file_button, field.remove_button)
            else:
                QWidget.setTabOrder(field.key_input, field.value_input)
                QWidget.setTabOrder(field.value_input, field.remove_button)

            if index < len(fields) - 1:
                next_field = fields[index + 1]

                if isinstance(next_field, TextOrFileDynamicField):
                    QWidget.setTabOrder(
                        field.remove_button,
                        next_field.text_radio,
                    )
                else:
                    QWidget.setTabOrder(
                        field.remove_button,
                        next_field.enable_checkbox,
                    )
