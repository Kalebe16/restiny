from pathlib import Path

from PySide6.QtCore import QLocale, Qt, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from qtmonaco import Monaco

from restiny.enums import AuthMode, BodyMode, BodyRawLanguage
from restiny.widgets.dynamic_fields import (
    DynamicFields,
    TextDynamicField,
    TextOrFileDynamicField,
)
from restiny.widgets.password_input import PasswordInput


class RequestArea(QWidget):
    sig_edited = Signal()

    def __init__(self):
        super().__init__()

        # Tabs
        self.tabs = QTabWidget()
        headers_tab = QWidget()
        params_tab = QWidget()
        auth_tab = QWidget()
        body_tab = QWidget()
        options_tab = QWidget()

        # Headers tab
        self.headers_dynamic_fields = DynamicFields(
            fields=[TextDynamicField()]
        )

        headers_layout = QVBoxLayout(headers_tab)
        headers_layout.addWidget(self.headers_dynamic_fields)

        # Params tab
        self.params_dynamic_fields = DynamicFields(fields=[TextDynamicField()])

        params_layout = QVBoxLayout(params_tab)
        params_layout.addWidget(self.params_dynamic_fields)

        # Auth
        self.auth_stack = QStackedWidget()

        # Basic Auth
        self.auth_basic_username_input = QLineEdit()
        self.auth_basic_username_input.setPlaceholderText('Username')

        self.auth_basic_password_input = PasswordInput()
        self.auth_basic_password_input.setPlaceholderText('Password')

        basic_widget = QWidget()
        basic_layout = QVBoxLayout(basic_widget)

        basic_first_row = QHBoxLayout()
        basic_first_row.addWidget(self.auth_basic_username_input)
        basic_first_row.addWidget(self.auth_basic_password_input)

        basic_layout.addLayout(basic_first_row)
        basic_layout.addStretch()

        self.auth_stack.addWidget(basic_widget)

        # Bearer Auth
        self.auth_bearer_token_input = PasswordInput()
        self.auth_bearer_token_input.setPlaceholderText('Token')

        bearer_widget = QWidget()
        bearer_layout = QVBoxLayout(bearer_widget)

        bearer_first_row = QHBoxLayout()
        bearer_first_row.addWidget(self.auth_bearer_token_input)

        bearer_layout.addLayout(bearer_first_row)
        bearer_layout.addStretch()

        self.auth_stack.addWidget(bearer_widget)

        # API Key Auth
        self.auth_api_key_where_combobox = QComboBox()
        self.auth_api_key_where_combobox.addItems(['header', 'param'])
        self.auth_api_key_key_input = QLineEdit()
        self.auth_api_key_key_input.setPlaceholderText('Key')
        self.auth_api_key_value_input = QLineEdit()
        self.auth_api_key_value_input.setPlaceholderText('Value')

        api_key_widget = QWidget()
        api_key_layout = QVBoxLayout(api_key_widget)

        api_key_first_row = QHBoxLayout()
        api_key_first_row.addWidget(self.auth_api_key_where_combobox)
        api_key_first_row.addWidget(self.auth_api_key_key_input)
        api_key_first_row.addWidget(self.auth_api_key_value_input)

        api_key_layout.addLayout(api_key_first_row)
        api_key_layout.addStretch()

        self.auth_stack.addWidget(api_key_widget)

        # Digest Auth
        self.auth_digest_username_input = QLineEdit()
        self.auth_digest_username_input.setPlaceholderText('Username')

        self.auth_digest_password_input = PasswordInput()
        self.auth_digest_password_input.setPlaceholderText('Password')

        digest_widget = QWidget()
        digest_layout = QVBoxLayout(digest_widget)

        digest_first_row = QHBoxLayout()
        digest_first_row.addWidget(self.auth_digest_username_input)
        digest_first_row.addWidget(self.auth_digest_password_input)

        digest_layout.addLayout(digest_first_row)
        digest_layout.addStretch()

        self.auth_stack.addWidget(digest_widget)

        self.auth_enabled_checkbox = QCheckBox()
        self.auth_enabled_checkbox.setStyleSheet("""
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
        }
        """)
        self.auth_mode_combobox = QComboBox()
        self.auth_mode_combobox.addItems([mode for mode in AuthMode])
        self.auth_mode_combobox.currentIndexChanged.connect(
            self.auth_stack.setCurrentIndex
        )

        first_row = QHBoxLayout()
        first_row.addWidget(self.auth_enabled_checkbox)
        first_row.addWidget(self.auth_mode_combobox, 1)

        # Layout do tab de Auth
        auth_layout = QVBoxLayout(auth_tab)
        auth_layout.addLayout(first_row)
        auth_layout.addWidget(self.auth_stack, 1)

        # Body
        self.body_enable_checkbox = QCheckBox()
        self.body_enable_checkbox.setChecked(False)
        self.body_enable_checkbox.setStyleSheet("""
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
        }
        """)

        self.body_mode_combobox = QComboBox()
        self.body_mode_combobox.addItems(
            ['raw', 'file', 'form_urlencoded', 'form_multipart']
        )

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

        self.body_stack = QStackedWidget()

        # Raw
        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        raw_layout.addWidget(self.body_text_editor, 1)

        self.body_raw_language_combobox = QComboBox()
        self.body_raw_language_combobox.addItems(
            [language for language in BodyRawLanguage]
        )
        self.body_raw_language_combobox.currentTextChanged.connect(
            self._on_body_raw_language_changed
        )

        self.body_indent_size_combobox = QComboBox()
        self.body_indent_size_combobox.addItems(['2', '4', '8'])
        self.body_indent_size_combobox.currentTextChanged.connect(
            self._on_indent_size_changed
        )

        raw_controls = QHBoxLayout()
        raw_controls.addWidget(self.body_raw_language_combobox, 1)
        raw_controls.addWidget(self.body_indent_size_combobox, 1)

        raw_layout.addLayout(raw_controls)
        self.body_stack.addWidget(raw_widget)

        # File
        self.file_input = QLineEdit()
        self.file_input.setDisabled(True)
        self.file_button = QPushButton('Browse')
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_input)
        file_row.addWidget(self.file_button)
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        file_layout.addLayout(file_row)
        file_layout.addStretch()
        self.body_stack.addWidget(file_widget)

        # Form urlencoded
        self.urlencoded_dynamic_fields = DynamicFields(
            fields=[TextDynamicField()]
        )
        urlencoded_widget = QWidget()
        urlencoded_layout = QVBoxLayout(urlencoded_widget)
        urlencoded_layout.addWidget(self.urlencoded_dynamic_fields)
        urlencoded_layout.addStretch()
        self.body_stack.addWidget(urlencoded_widget)

        # Form multipart
        self.multipart_dynamic_fields = DynamicFields(
            fields=[TextOrFileDynamicField()]
        )
        multipart_widget = QWidget()
        multipart_layout = QVBoxLayout(multipart_widget)
        multipart_layout.addWidget(
            self.multipart_dynamic_fields, 0, Qt.AlignTop
        )
        multipart_layout.addStretch()
        self.body_stack.addWidget(multipart_widget)

        # Conecta combobox ao stack
        self.body_mode_combobox.currentIndexChanged.connect(
            self.body_stack.setCurrentIndex
        )

        # Layout do body
        body_first_line = QHBoxLayout()
        body_first_line.addWidget(self.body_enable_checkbox)
        body_first_line.addWidget(self.body_mode_combobox, 1)

        body_layout = QVBoxLayout(body_tab)
        body_layout.addLayout(body_first_line)
        body_layout.addWidget(self.body_stack, 1)

        # Options
        self.options_timeout_label = QLabel()
        self.options_timeout_label.setText('Timeout')
        self.options_timeout_input = QLineEdit()
        self.options_timeout_input.setPlaceholderText('5.5')
        validator = QDoubleValidator(0.0, 100.0, 2)
        validator.setLocale(QLocale.c())
        self.options_timeout_input.setValidator(validator)

        self.options_follow_redirects_checkbox = QCheckBox()
        self.options_follow_redirects_checkbox.setStyleSheet("""
QCheckBox::indicator {
    width: 20px;
    height: 20px;
}
""")
        self.options_follow_redirects_label = QLabel()
        self.options_follow_redirects_label.setText('Follow redirects')

        self.options_verify_ssl_checkbox = QCheckBox()
        self.options_verify_ssl_checkbox.setStyleSheet("""
QCheckBox::indicator {
    width: 20px;
    height: 20px;
}
""")
        self.options_verify_ssl_label = QLabel()
        self.options_verify_ssl_label.setText('Verify SSL')

        self.options_attach_cookies_checkbox = QCheckBox()
        self.options_attach_cookies_checkbox.setStyleSheet("""
QCheckBox::indicator {
    width: 20px;
    height: 20px;
}
""")
        self.attach_cookies_label = QLabel()
        self.attach_cookies_label.setText('Attach cookies (store and send)')

        options_first_line = QHBoxLayout()
        options_first_line.addWidget(self.options_timeout_label)
        options_first_line.addWidget(self.options_timeout_input, 1)

        options_second_line = QHBoxLayout()
        options_second_line.addWidget(self.options_follow_redirects_checkbox)
        options_second_line.addWidget(self.options_follow_redirects_label)
        options_second_line.addStretch()

        options_third_line = QHBoxLayout()
        options_third_line.addWidget(self.options_verify_ssl_checkbox)
        options_third_line.addWidget(self.options_verify_ssl_label)
        options_third_line.addStretch()

        options_fourth_line = QHBoxLayout()
        options_fourth_line.addWidget(self.options_attach_cookies_checkbox)
        options_fourth_line.addWidget(self.attach_cookies_label)
        options_fourth_line.addStretch()

        options_layout = QVBoxLayout(options_tab)
        options_layout.addLayout(options_first_line)
        options_layout.addLayout(options_second_line)
        options_layout.addLayout(options_third_line)
        options_layout.addLayout(options_fourth_line)
        options_layout.addStretch()

        # Register tabs
        self.tabs.addTab(headers_tab, 'Headers')
        self.tabs.addTab(params_tab, 'Params')
        self.tabs.addTab(auth_tab, 'Auth')
        self.tabs.addTab(body_tab, 'Body')
        self.tabs.addTab(options_tab, 'Options')

        # GroupBox
        self.group_box = QGroupBox()
        self.group_box.setTitle('Request')

        group_layout = QVBoxLayout(self.group_box)
        group_layout.addWidget(self.tabs)

        # Main layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.group_box)

        self.file_button.clicked.connect(self._on_browse_file)

        self.headers_dynamic_fields.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.params_dynamic_fields.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_basic_username_input.textChanged.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_basic_password_input.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_bearer_token_input.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_api_key_where_combobox.currentTextChanged.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_api_key_key_input.textEdited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_api_key_value_input.textEdited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_digest_username_input.textEdited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_digest_password_input.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_enabled_checkbox.toggled.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_mode_combobox.currentTextChanged.connect(
            lambda: self.sig_edited.emit()
        )
        self.body_enable_checkbox.toggled.connect(
            lambda: self.sig_edited.emit()
        )
        self.body_mode_combobox.currentTextChanged.connect(
            lambda: self.sig_edited.emit()
        )
        self.body_text_editor.text_changed.connect(
            lambda: self.sig_edited.emit()
        )
        self.body_raw_language_combobox.currentTextChanged.connect(
            lambda: self.sig_edited.emit()
        )
        self.file_input.textChanged.connect(lambda: self.sig_edited.emit())
        self.urlencoded_dynamic_fields.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.multipart_dynamic_fields.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.options_timeout_input.textChanged.connect(
            lambda: self.sig_edited.emit()
        )
        self.options_follow_redirects_checkbox.toggled.connect(
            lambda: self.sig_edited.emit()
        )
        self.options_verify_ssl_checkbox.toggled.connect(
            lambda: self.sig_edited.emit()
        )
        self.options_attach_cookies_checkbox.toggled.connect(
            lambda: self.sig_edited.emit()
        )

    def clear_data(self) -> None:
        # Headers e Params
        self.headers_dynamic_fields.clear_data()
        self.params_dynamic_fields.clear_data()

        # Auth
        self.auth_enabled_checkbox.setChecked(False)
        self.auth_mode_combobox.setCurrentText(AuthMode.BASIC)
        self.auth_basic_username_input.setText('')
        self.auth_basic_password_input.setText('')
        self.auth_bearer_token_input.setText('')
        self.auth_api_key_where_combobox.setCurrentText('header')
        self.auth_api_key_key_input.setText('')
        self.auth_api_key_value_input.setText('')
        self.auth_digest_username_input.setText('')
        self.auth_digest_password_input.setText('')

        # Body
        self.body_enable_checkbox.setChecked(False)
        self.body_mode_combobox.setCurrentText(BodyMode.RAW)
        self.body_text_editor.set_text('')
        self.body_raw_language_combobox.setCurrentText(BodyRawLanguage.PLAIN)
        self.body_indent_size_combobox.setCurrentText('2')
        self.file_input.clear()
        self.urlencoded_dynamic_fields.clear_data()
        self.multipart_dynamic_fields.clear_data()

        # Options
        self.options_timeout_input.clear()
        self.options_follow_redirects_checkbox.setChecked(False)
        self.options_verify_ssl_checkbox.setChecked(False)
        self.options_attach_cookies_checkbox.setChecked(False)

    def get_data(self) -> dict:
        auth_enabled = self.auth_enabled_checkbox.isChecked()
        auth_mode = self.auth_mode_combobox.currentText()
        auth = None
        if auth_mode == AuthMode.BASIC:
            auth = {
                'username': self.auth_basic_username_input.text(),
                'password': self.auth_basic_password_input.text(),
            }
        elif auth_mode == AuthMode.BEARER:
            auth = {'token': self.auth_bearer_token_input.text()}
        elif auth_mode == AuthMode.API_KEY:
            auth = {
                'where': self.auth_api_key_where_combobox.currentText(),
                'key': self.auth_api_key_key_input.text(),
                'value': self.auth_api_key_value_input.text(),
            }
        elif auth_mode == AuthMode.DIGEST:
            auth = {
                'username': self.auth_digest_username_input.text(),
                'password': self.auth_digest_password_input.text(),
            }

        body_enabled = self.body_enable_checkbox.isChecked()
        body_mode = self.body_mode_combobox.currentText()
        body = None
        if body_mode == BodyMode.RAW:
            body = {
                'language': self.body_raw_language_combobox.currentText(),
                'value': self.body_text_editor.get_text(),
            }
        elif body_mode == BodyMode.FILE:
            body = {
                'file': (
                    Path(self.file_input.text())
                    if self.file_input.text()
                    else None
                ),
            }
        elif body_mode == BodyMode.FORM_URLENCODED:
            body = {
                'fields': [
                    field.get_data()
                    for field in self.urlencoded_dynamic_fields.fields
                ],
            }
        elif body_mode == BodyMode.FORM_MULTIPART:
            body = {
                'fields': [
                    field.get_data()
                    for field in self.multipart_dynamic_fields.fields
                ],
            }

        return {
            'headers': [
                field.get_data()
                for field in self.headers_dynamic_fields.fields
                if field.is_filled
            ],
            'params': [
                field.get_data()
                for field in self.params_dynamic_fields.fields
                if field.is_filled
            ],
            'auth_enabled': auth_enabled,
            'auth_mode': auth_mode,
            'auth': auth,
            'body_enabled': body_enabled,
            'body_mode': body_mode,
            'body': body,
            'options': {
                'timeout': float(self.options_timeout_input.text() or 0),
                'follow_redirects': self.options_follow_redirects_checkbox.isChecked(),
                'verify_ssl': self.options_verify_ssl_checkbox.isChecked(),
                'attach_cookies': self.options_attach_cookies_checkbox.isChecked(),
            },
        }

    def set_data(self, data: dict) -> None:
        for field in data.get('headers', []):
            self.headers_dynamic_fields.add_field(
                TextDynamicField(
                    enabled=field['enabled'],
                    key=field['key'],
                    value=field['value'],
                )
            )

        for field in data.get('params', []):
            self.params_dynamic_fields.add_field(
                TextDynamicField(
                    enabled=field['enabled'],
                    key=field['key'],
                    value=field['value'],
                )
            )

        self.auth_enabled_checkbox.setChecked(data['auth_enabled'])
        self.auth_mode_combobox.setCurrentText(data['auth_mode'])
        if data['auth_mode'] == AuthMode.BASIC:
            self.auth_basic_username_input.setText(data['auth']['username'])
            self.auth_basic_password_input.setText(data['auth']['password'])
        elif data['auth_mode'] == AuthMode.BEARER:
            self.auth_bearer_token_input.setText(data['auth']['token'])
        elif data['auth_mode'] == AuthMode.API_KEY:
            self.auth_api_key_where_combobox.setCurrentText(
                data['auth']['where']
            )
            self.auth_api_key_key_input.setText(data['auth']['key'])
            self.auth_api_key_value_input.setText(data['auth']['value'])
        elif data['auth_mode'] == AuthMode.DIGEST:
            self.auth_digest_username_input.setText(data['auth']['username'])
            self.auth_digestpassword_input.setText(data['auth']['password'])

        self.body_enable_checkbox.setChecked(data['body_enabled'])
        self.body_mode_combobox.setCurrentText(data['body_mode'])
        if data['body_mode'] == BodyMode.RAW:
            self.body_raw_language_combobox.setCurrentText(
                data['body']['language']
            )
            self.body_text_editor.set_text(data['body']['value'])
        elif data['body_mode'] == BodyMode.FILE:
            self.file_input.setText(str(data['body']['file']))
        elif data['body_mode'] == BodyMode.FORM_URLENCODED:
            for field in data['body']['fields']:
                self.urlencoded_dynamic_fields.add_field(
                    TextDynamicField(
                        enabled=field['enabled'],
                        key=field['key'],
                        value=field['value'],
                    )
                )
        elif data['body_mode'] == BodyMode.FORM_MULTIPART:
            for field in data['body']['fields']:
                self.multipart_dynamic_fields.add_field(
                    TextOrFileDynamicField(
                        value_kind=field['value_kind'],
                        enabled=field['enabled'],
                        key=field['key'],
                        value=str(field['value']) if field['value'] else '',
                    )
                )

        self.options_timeout_input.setText(str(data['options']['timeout']))
        self.options_follow_redirects_checkbox.setChecked(
            data['options']['follow_redirects']
        )
        self.options_verify_ssl_checkbox.setChecked(
            data['options']['verify_ssl']
        )
        self.options_attach_cookies_checkbox.setChecked(
            data['options']['attach_cookies']
        )

    def _on_body_raw_language_changed(self, text_type: str) -> None:
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

    def _on_browse_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, 'Select file')

        if not filename:
            return

        self.file_input.setText(filename)
