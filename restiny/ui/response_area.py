from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from qtmonaco import Monaco

from restiny.enums import BodyRawLanguage

NO_RESPONSE_TEXT = "No response yet. Press 'Send' or 'Download' to continue."


class ResponseArea(QWidget):
    def __init__(self):
        super().__init__()
        self._is_loading = False

        self.no_response_label = QLabel()
        self.no_response_label.setText(NO_RESPONSE_TEXT)
        self.no_response_label.setAlignment(Qt.AlignCenter)

        # Tabs
        self.tabs = QTabWidget()
        headers_tab = QWidget()
        body_tab = QWidget()

        # Headers tab
        self.headers_table = QTableWidget()
        self.headers_table.setColumnCount(2)
        self.headers_table.setHorizontalHeaderLabels(['key', 'value'])
        header = self.headers_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        headers_layout = QVBoxLayout(headers_tab)
        headers_layout.addWidget(self.headers_table, 1)

        # Body tab
        self.body_text_editor = Monaco()
        self.body_text_editor.set_language('plaintext')
        self.body_text_editor.set_theme('vs-dark')
        self.body_text_editor.set_minimap_enabled(True)
        self.body_text_editor._connector.send(
            'update_editor_options',
            {
                'tabSize': 2,
                'insertSpaces': True,
                'detectIndentation': False,
            },
        )

        self.body_raw_language_combobox = QComboBox()
        self.body_raw_language_combobox.addItems(
            [language for language in BodyRawLanguage]
        )
        self.body_raw_language_combobox.currentTextChanged.connect(
            self._on_text_type_changed
        )

        body_layout = QVBoxLayout(body_tab)
        body_layout.addWidget(self.body_text_editor)
        body_layout.addWidget(self.body_raw_language_combobox)

        self.tabs.addTab(headers_tab, 'Headers')
        self.tabs.addTab(body_tab, 'Body')

        self.group_box = QGroupBox()
        self.group_box.setTitle('Response')

        group_layout = QVBoxLayout(self.group_box)
        group_layout.addWidget(self.tabs)
        group_layout.addWidget(self.no_response_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self.group_box)
        self.show_empty()

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @is_loading.setter
    def is_loading(self, value: bool) -> None:
        if value:
            self.no_response_label.setText('Loading...')
            self.show_empty()
        else:
            self.no_response_label.setText(NO_RESPONSE_TEXT)

    def show_empty(self) -> None:
        self.no_response_label.show()
        self.tabs.hide()

    def show_response(self) -> None:
        self.no_response_label.hide()
        self.tabs.show()

    def set_data(self, data: dict) -> None:
        self.group_box.setTitle(
            f'Response - {data["status"].value} {data["status"].phrase} '
            f'({data["content_size"]} bytes in {data["elapsed_time"]} seconds)'
        )

        self.headers_table.clearContents()
        self.headers_table.setRowCount(len(data['headers']))
        for row, (header_key, header_value) in enumerate(
            data['headers'].items()
        ):
            self.headers_table.setItem(row, 0, QTableWidgetItem(header_key))
            self.headers_table.setItem(row, 1, QTableWidgetItem(header_value))

        self.body_text_editor.set_text(
            value=data['body_raw'], language=data['body_raw_language']
        )
        self.body_raw_language_combobox.setCurrentText(
            data['body_raw_language']
        )

    def clear_data(self):
        self.group_box.setTitle('Response')
        self.headers_table.clearContents()
        self.body_text_editor.set_text(value='')

    def _on_text_type_changed(self, text_type: str) -> None:
        self.body_text_editor.set_language(language=text_type)

    def _on_indent_size_changed(self, indent_size: str) -> None:
        self.body_text_editor._connector.send(
            'update_editor_options',
            {
                'tabSize': int(indent_size),
                'insertSpaces': True,
                'detectIndentation': False,
            },
        )
