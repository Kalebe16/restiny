import markdown
from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtGui import QDesktopServices, QPalette
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from qtmonaco import Monaco

from restiny.data.repos import SettingsSQLRepo
from restiny.enums import AuthMode
from restiny.widgets.dynamic_fields import DynamicFields, TextDynamicField
from restiny.widgets.password_input import PasswordInput


class PreviewPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationTypeLinkClicked:
            if url.scheme() in ('http', 'https'):
                QDesktopServices.openUrl(url)
                return False

        return super().acceptNavigationRequest(
            url,
            navigation_type,
            is_main_frame,
        )


class FolderArea(QWidget):
    sig_edited = Signal()
    sig_seted_data = Signal()

    def __init__(self, settings_repo: SettingsSQLRepo):
        super().__init__()

        self.settings_repo = settings_repo

        self.tabs = QTabWidget()
        self.documentation_tab = QWidget()
        self.headers_tab = QWidget()
        self.auth_tab = QWidget()

        self.tabs.addTab(self.documentation_tab, 'Documentation')
        self.tabs.addTab(self.headers_tab, 'Headers')
        self.tabs.addTab(self.auth_tab, 'Auth')

        self.docs_tabs = QTabWidget()

        self.docs_editor = Monaco()
        self.docs_editor.set_language('markdown')
        self.docs_editor.set_theme('vs-dark')

        self.preview_browser = QWebEngineView()
        self.preview_browser.setPage(PreviewPage(self.preview_browser))

        self.docs_editor_tab = QWidget()
        docs_editor_layout = QVBoxLayout(self.docs_editor_tab)
        docs_editor_layout.setContentsMargins(0, 0, 0, 0)
        docs_editor_layout.addWidget(self.docs_editor)

        self.docs_preview_tab = QWidget()
        docs_preview_layout = QVBoxLayout(self.docs_preview_tab)
        docs_preview_layout.setContentsMargins(0, 0, 0, 0)
        docs_preview_layout.addWidget(self.preview_browser)

        self.docs_tabs.addTab(self.docs_preview_tab, 'Preview')
        self.docs_tabs.addTab(self.docs_editor_tab, 'Editor')

        documentation_layout = QVBoxLayout(self.documentation_tab)
        documentation_layout.addWidget(self.docs_tabs)

        self.headers_dynamic_fields = DynamicFields(
            fields=[TextDynamicField()]
        )

        headers_layout = QVBoxLayout(self.headers_tab)
        headers_layout.addWidget(self.headers_dynamic_fields)

        self.auth_mode_combobox = QComboBox()
        self.auth_mode_combobox.addItems(
            [mode for mode in AuthMode if mode != AuthMode.INHERITED]
        )

        self.auth_stack = QStackedWidget()

        self.auth_basic_username_input = QLineEdit()
        self.auth_basic_username_input.setPlaceholderText('Username')

        self.auth_basic_password_input = PasswordInput()
        self.auth_basic_password_input.setPlaceholderText('Password')

        self.auth_basic_widget = QWidget()

        basic_row = QHBoxLayout()
        basic_row.addWidget(self.auth_basic_username_input)
        basic_row.addWidget(self.auth_basic_password_input)

        basic_layout = QVBoxLayout(self.auth_basic_widget)
        basic_layout.addLayout(basic_row)
        basic_layout.addStretch()

        self.auth_bearer_token_input = PasswordInput()
        self.auth_bearer_token_input.setPlaceholderText('Token')

        self.auth_bearer_widget = QWidget()

        bearer_row = QHBoxLayout()
        bearer_row.addWidget(self.auth_bearer_token_input)

        bearer_layout = QVBoxLayout(self.auth_bearer_widget)
        bearer_layout.addLayout(bearer_row)
        bearer_layout.addStretch()

        self.auth_api_key_where_combobox = QComboBox()
        self.auth_api_key_where_combobox.addItems(['header', 'param'])

        self.auth_api_key_key_input = QLineEdit()
        self.auth_api_key_key_input.setPlaceholderText('Key')

        self.auth_api_key_value_input = PasswordInput()
        self.auth_api_key_value_input.setPlaceholderText('Value')

        self.auth_api_key_widget = QWidget()

        api_key_row = QHBoxLayout()
        api_key_row.addWidget(self.auth_api_key_where_combobox)
        api_key_row.addWidget(self.auth_api_key_key_input)
        api_key_row.addWidget(self.auth_api_key_value_input)

        api_key_layout = QVBoxLayout(self.auth_api_key_widget)
        api_key_layout.addLayout(api_key_row)
        api_key_layout.addStretch()

        self.auth_digest_username_input = QLineEdit()
        self.auth_digest_username_input.setPlaceholderText('Username')

        self.auth_digest_password_input = PasswordInput()
        self.auth_digest_password_input.setPlaceholderText('Password')

        self.auth_digest_widget = QWidget()

        digest_row = QHBoxLayout()
        digest_row.addWidget(self.auth_digest_username_input)
        digest_row.addWidget(self.auth_digest_password_input)

        digest_layout = QVBoxLayout(self.auth_digest_widget)
        digest_layout.addLayout(digest_row)
        digest_layout.addStretch()

        self.auth_stack.addWidget(self.auth_basic_widget)
        self.auth_stack.addWidget(self.auth_bearer_widget)
        self.auth_stack.addWidget(self.auth_api_key_widget)
        self.auth_stack.addWidget(self.auth_digest_widget)

        auth_header_layout = QHBoxLayout()
        auth_header_layout.addWidget(self.auth_mode_combobox, 1)

        auth_layout = QVBoxLayout(self.auth_tab)
        auth_layout.addLayout(auth_header_layout)
        auth_layout.addWidget(self.auth_stack, 1)

        self.group_box = QGroupBox('Folder')

        group_box_layout = QVBoxLayout(self.group_box)
        group_box_layout.addWidget(self.tabs)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group_box)

        self.docs_tabs.currentChanged.connect(lambda: self.update_preview())
        self.auth_mode_combobox.currentIndexChanged.connect(
            self.auth_stack.setCurrentIndex
        )

        self.docs_editor.text_changed.connect(lambda: self.sig_edited.emit())
        self.headers_dynamic_fields.sig_edited.connect(
            lambda: self.sig_edited.emit()
        )
        self.auth_mode_combobox.currentTextChanged.connect(
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
        self.auth_api_key_key_input.textChanged.connect(
            lambda: self.sig_edited.emit()
        )

    def update_preview(self):
        markdown_text = self.docs_editor.get_text()

        palette = self.palette()
        background_color = palette.color(QPalette.Base).name()
        text_color = palette.color(QPalette.Text).name()
        border_color = palette.color(QPalette.Mid).name()
        accent_color = self.settings_repo.get().data.accent_color

        html = markdown.markdown(
            markdown_text,
            extensions=[
                'tables',
                'toc',
                'admonition',
                'attr_list',
                'def_list',
                'footnotes',
                'md_in_html',
                'sane_lists',
                'pymdownx.superfences',
                'pymdownx.highlight',
                'pymdownx.inlinehilite',
                'pymdownx.tasklist',
                'pymdownx.tilde',
                'pymdownx.mark',
                'pymdownx.keys',
                'pymdownx.caret',
                'pymdownx.details',
                'pymdownx.smartsymbols',
                'pymdownx.emoji',
            ],
            extension_configs={
                'toc': {
                    'permalink': True,
                    'slugify': lambda value, separator: (
                        value.lower()
                        .replace(' ', separator)
                        .replace('/', separator)
                    ),
                },
                'pymdownx.highlight': {
                    'anchor_linenums': True,
                    'line_spans': 'line',
                    'pygments_lang_class': True,
                },
                'pymdownx.tasklist': {
                    'custom_checkbox': True,
                    'clickable_checkbox': False,
                },
            },
        )
        styled_html = f"""
<html>
<head>
<style>
body {{
    margin: 16px;
    background: {background_color};
    color: {text_color};
    font-family: sans-serif;
    line-height: 1.6;
}}

a {{
    color: {accent_color};
}}

pre {{
    padding: 12px;
    background: rgba(127,127,127,.12);
    border-radius: 6px;
    overflow-x: auto;
}}

code {{
    font-family: monospace;
}}

table {{
    border-collapse: collapse;
    width: 100%;
}}

th, td {{
    border: 1px solid {border_color};
    padding: 6px 10px;
}}

th {{
    background: rgba(127,127,127,.08);
}}

blockquote {{
    margin: 0;
    padding-left: 12px;
    border-left: 4px solid {accent_color};
}}

img {{
    max-width: 100%;
}}

.admonition {{
    padding: 10px;
    border-left: 4px solid {accent_color};
    background: rgba(127,127,127,.08);
    border-radius: 4px;
}}

.admonition-title {{
    font-weight: bold;
}}
</style>
</head>
<body>
{html}
</body>
</html>
                """
        self.preview_browser.setHtml(styled_html)

    def clear_data(self):
        self.headers_dynamic_fields.clear_data()
        self.auth_mode_combobox.setCurrentText(AuthMode.BASIC)
        self.auth_basic_username_input.setText('')
        self.auth_basic_password_input.setText('')
        self.auth_bearer_token_input.setText('')
        self.auth_api_key_where_combobox.setCurrentText('header')
        self.auth_api_key_key_input.setText('')
        self.auth_api_key_value_input.setText('')
        self.auth_digest_username_input.setText('')
        self.auth_digest_password_input.setText('')
        self.docs_editor.set_text('')

    def get_data(self) -> dict:
        headers = [
            field.get_data()
            for field in self.headers_dynamic_fields.fields
            if field.is_filled
        ]
        auth_mode = self.auth_mode_combobox.currentText()
        documentation = self.docs_editor.get_text()
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
        return {
            'headers': headers,
            'auth_mode': auth_mode,
            'auth': auth,
            'documentation': documentation,
        }

    def set_data(self, data: dict):
        with QSignalBlocker(self):
            self.headers_dynamic_fields.clear_data()
            for field in data['headers']:
                self.headers_dynamic_fields.add_field(
                    TextDynamicField(
                        enabled=field['enabled'],
                        key=field['key'],
                        value=field['value'],
                    )
                )
            self.auth_mode_combobox.setCurrentText(data['auth_mode'])
            if data['auth_mode'] == AuthMode.BASIC:
                self.auth_basic_username_input.setText(
                    data['auth']['username']
                )
                self.auth_basic_password_input.setText(
                    data['auth']['password']
                )
            elif data['auth_mode'] == AuthMode.BEARER:
                self.auth_bearer_token_input.setText(data['auth']['token'])
            elif data['auth_mode'] == AuthMode.API_KEY:
                self.auth_api_key_where_combobox.setCurrentText(
                    data['auth']['where']
                )
                self.auth_api_key_key_input.setText(data['auth']['key'])
                self.auth_api_key_value_input.setText(data['auth']['value'])
            elif data['auth_mode'] == AuthMode.DIGEST:
                self.auth_digest_username_input.setText(
                    data['auth']['username']
                )
                self.auth_digest_password_input.setText(
                    data['auth']['password']
                )

            self.docs_editor.set_text(data['documentation'])
            self.update_preview()
        self.sig_seted_data.emit()
