from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    ContentSwitcher,
    Label,
    Select,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

from restiny.enums import AuthMode, BodyMode, BodyRawLanguage
from restiny.widgets import (
    CustomInput,
    CustomTextArea,
    DynamicFields,
    PasswordInput,
    PathChooser,
    TextDynamicField,
    TextOrFileDynamicField,
)


class RequestArea(Static):
    ALLOW_MAXIMIZE = True
    focusable = True
    BORDER_TITLE = 'Request'
    DEFAULT_CSS = """
    RequestArea {
        width: 1fr;
        height: 1fr;
        border: heavy black;
        border-title-color: gray;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane('Headers'):
                yield DynamicFields(
                    fields=[TextDynamicField(enabled=False, key='', value='')],
                    id='headers',
                )
            with TabPane('Params'):
                yield DynamicFields(
                    fields=[TextDynamicField(enabled=False, key='', value='')],
                    id='params',
                )
            with TabPane('Auth'):
                with Horizontal(classes='h-auto'):
                    yield Switch(tooltip='Enabled', id='auth-enabled')
                    yield Select(
                        (
                            ('Basic', AuthMode.BASIC),
                            ('Bearer', AuthMode.BEARER),
                            ('API Key', AuthMode.API_KEY),
                            ('Digest', AuthMode.DIGEST),
                        ),
                        allow_blank=False,
                        tooltip='Auth mode',
                        id='auth-mode',
                    )
                with ContentSwitcher(
                    initial='auth-basic', id='auth-mode-switcher'
                ):
                    with Horizontal(id='auth-basic', classes='mt-1'):
                        yield CustomInput(
                            placeholder='Username',
                            select_on_focus=False,
                            classes='w-1fr',
                            id='auth-basic-username',
                        )
                        yield PasswordInput(
                            placeholder='Password',
                            select_on_focus=False,
                            classes='w-2fr',
                            id='auth-basic-password',
                        )
                    with Horizontal(id='auth-bearer', classes='mt-1'):
                        yield PasswordInput(
                            placeholder='Token',
                            select_on_focus=False,
                            id='auth-bearer-token',
                        )
                    with Horizontal(id='auth-api-key', classes='mt-1'):
                        yield Select(
                            (('Header', 'header'), ('Param', 'param')),
                            allow_blank=False,
                            tooltip='Where',
                            classes='w-1fr',
                            id='auth-api-key-where',
                        )
                        yield CustomInput(
                            placeholder='Key',
                            classes='w-2fr',
                            id='auth-api-key-key',
                        )
                        yield PasswordInput(
                            placeholder='Value',
                            classes='w-3fr',
                            id='auth-api-key-value',
                        )

                    with Horizontal(id='auth-digest', classes='mt-1'):
                        yield CustomInput(
                            placeholder='Username',
                            select_on_focus=False,
                            classes='w-1fr',
                            id='auth-digest-username',
                        )
                        yield PasswordInput(
                            placeholder='Password',
                            select_on_focus=False,
                            classes='w-2fr',
                            id='auth-digest-password',
                        )

            with TabPane('Body'):
                with Horizontal(classes='h-auto'):
                    yield Switch(id='body-enabled', tooltip='Send body?')
                    yield Select(
                        (
                            ('Raw', BodyMode.RAW),
                            ('File', BodyMode.FILE),
                            ('Form (urlencoded)', BodyMode.FORM_URLENCODED),
                            ('Form (multipart)', BodyMode.FORM_MULTIPART),
                        ),
                        allow_blank=False,
                        tooltip='Body mode',
                        id='body-mode',
                    )
                with ContentSwitcher(
                    id='body-mode-switcher',
                    initial='body-mode-raw',
                    classes='h-1fr',
                ):
                    with Container(id='body-mode-raw', classes='pt-1'):
                        yield Select(
                            (
                                ('Plain', BodyRawLanguage.PLAIN),
                                ('JSON', BodyRawLanguage.JSON),
                                ('YAML', BodyRawLanguage.YAML),
                                ('XML', BodyRawLanguage.XML),
                                ('HTML', BodyRawLanguage.HTML),
                            ),
                            allow_blank=False,
                            tooltip='Text type',
                            id='body-raw-language',
                        )
                        yield CustomTextArea.code_editor(
                            language='json', id='body-raw', classes='mt-1'
                        )
                    with Horizontal(
                        id='body-mode-file', classes='h-auto mt-1'
                    ):
                        yield PathChooser.file(id='body-file')
                    with Horizontal(
                        id='body-mode-form-urlencoded', classes='h-auto mt-1'
                    ):
                        yield DynamicFields(
                            [
                                TextDynamicField(
                                    enabled=False, key='', value=''
                                )
                            ],
                            id='body-form-urlencoded',
                        )
                    with Horizontal(
                        id='body-mode-form-multipart', classes='h-auto mt-1'
                    ):
                        yield DynamicFields(
                            [
                                TextOrFileDynamicField(
                                    enabled=False, key='', value=''
                                )
                            ],
                            id='body-form-multipart',
                        )

            with TabPane('Options'):
                with Horizontal(classes='h-auto'):
                    yield Label('Timeout', classes='pt-1 ml-1')
                    yield CustomInput(
                        '5.5',
                        placeholder='5.5',
                        select_on_focus=False,
                        type='number',
                        valid_empty=True,
                        classes='w-1fr',
                        id='options-timeout',
                    )
                with Horizontal(classes='mt-1 h-auto'):
                    yield Switch(id='options-follow-redirects')
                    yield Label('Follow redirects', classes='pt-1')
                with Horizontal(classes='h-auto'):
                    yield Switch(id='options-verify-ssl')
                    yield Label('Verify SSL', classes='pt-1')

    def on_mount(self) -> None:
        self.header_fields = self.query_one('#headers', DynamicFields)

        self.param_fields = self.query_one('#params', DynamicFields)

        self.auth_enabled_switch = self.query_one('#auth-enabled', Switch)
        self.auth_mode_switcher = self.query_one(
            '#auth-mode-switcher', ContentSwitcher
        )
        self.auth_mode_select = self.query_one('#auth-mode', Select)
        self.auth_basic_username_input = self.query_one(
            '#auth-basic-username', CustomInput
        )
        self.auth_basic_password_input = self.query_one(
            '#auth-basic-password', PasswordInput
        )
        self.auth_bearer_token_input = self.query_one(
            '#auth-bearer-token', PasswordInput
        )
        self.auth_api_key_key_input = self.query_one(
            '#auth-api-key-key', CustomInput
        )
        self.auth_api_key_value_input = self.query_one(
            '#auth-api-key-value', PasswordInput
        )
        self.auth_api_key_where_select = self.query_one(
            '#auth-api-key-where', Select
        )
        self.auth_digest_username_input = self.query_one(
            '#auth-digest-username', CustomInput
        )
        self.auth_digest_password_input = self.query_one(
            '#auth-digest-password', PasswordInput
        )

        self.body_enabled_switch = self.query_one('#body-enabled', Switch)
        self.body_mode_select = self.query_one('#body-mode', Select)
        self.body_mode_switcher = self.query_one(
            '#body-mode-switcher', ContentSwitcher
        )
        self.body_raw_editor = self.query_one('#body-raw', CustomTextArea)
        self.body_raw_language_select = self.query_one(
            '#body-raw-language', Select
        )
        self.body_file_path_chooser = self.query_one('#body-file', PathChooser)
        self.body_form_urlencoded_fields = self.query_one(
            '#body-form-urlencoded', DynamicFields
        )
        self.body_form_multipart_fields = self.query_one(
            '#body-form-multipart', DynamicFields
        )

        self.options_timeout_input = self.query_one(
            '#options-timeout', CustomInput
        )
        self.options_follow_redirects_switch = self.query_one(
            '#options-follow-redirects', Switch
        )
        self.options_verify_ssl_switch = self.query_one(
            '#options-verify-ssl', Switch
        )

    @property
    def headers(self) -> list[dict[str, str | bool]]:
        return [
            {
                'enabled': header.enabled,
                'key': header.key,
                'value': header.value,
            }
            for header in self.header_fields.fields
            if header.is_filled or header.enabled
        ]

    @headers.setter
    def headers(self, headers: list[dict[str, str | bool]]) -> None:
        for field in self.header_fields.fields:
            self.header_fields.remove_field(field=field)

        for header in headers:
            self.run_worker(
                self.header_fields.add_field(
                    field=TextDynamicField(
                        enabled=header['enabled'],
                        key=header['key'],
                        value=header['value'],
                    ),
                    before_last=True,
                )
            )

    @property
    def params(self) -> list[dict[str, str | bool]]:
        return [
            {
                'enabled': param.enabled,
                'key': param.key,
                'value': param.value,
            }
            for param in self.param_fields.fields
            if param.is_filled or param.enabled
        ]

    @params.setter
    def params(self, params: list[dict[str, str | bool]]) -> None:
        for field in self.param_fields.fields:
            self.param_fields.remove_field(field=field)

        for param in params:
            self.run_worker(
                self.param_fields.add_field(
                    field=TextDynamicField(
                        enabled=param['enabled'],
                        key=param['key'],
                        value=param['value'],
                    ),
                    before_last=True,
                )
            )

    @property
    def auth_enabled(self) -> bool:
        return self.auth_enabled_switch.value

    @auth_enabled.setter
    def auth_enabled(self, value: bool) -> None:
        self.auth_enabled_switch.value = value

    @property
    def auth_mode(self) -> AuthMode:
        return self.auth_mode_select.value

    @auth_mode.setter
    def auth_mode(self, value: AuthMode) -> None:
        self.auth_mode_select.value = value

    @property
    def auth_basic_username(self) -> str:
        return self.auth_basic_username_input.value

    @auth_basic_username.setter
    def auth_basic_username(self, value: str) -> None:
        self.auth_basic_username_input.value = value

    @property
    def auth_basic_password(self) -> str:
        return self.auth_basic_password_input.value

    @auth_basic_password.setter
    def auth_basic_password(self, value: str) -> None:
        self.auth_basic_password_input.value = value

    @property
    def auth_bearer_token(self) -> str:
        return self.auth_bearer_token_input.value

    @auth_bearer_token.setter
    def auth_bearer_token(self, value: str) -> None:
        self.auth_bearer_token_input.value = value

    @property
    def auth_api_key_key(self) -> str:
        return self.auth_api_key_key_input.value

    @auth_api_key_key.setter
    def auth_api_key_key(self, value: str) -> None:
        self.auth_api_key_key_input.value = value

    @property
    def auth_api_key_value(self) -> str:
        return self.auth_api_key_value_input.value

    @auth_api_key_value.setter
    def auth_api_key_value(self, value: str) -> None:
        self.auth_api_key_value_input.value = value

    @property
    def auth_api_key_where(self) -> str:
        return self.auth_api_key_where_select.value

    @auth_api_key_where.setter
    def auth_api_key_where(self, value: str) -> None:
        self.auth_api_key_where_select.value = value

    @property
    def auth_digest_username(self) -> str:
        return self.auth_digest_username_input.value

    @auth_digest_username.setter
    def auth_digest_username(self, value: str) -> None:
        self.auth_digest_username_input.value = value

    @property
    def auth_digest_password(self) -> str:
        return self.auth_digest_password_input.value

    @auth_digest_password.setter
    def auth_digest_password(self, value: str) -> None:
        self.auth_digest_password_input.value = value

    @property
    def body_enabled(self) -> bool:
        return self.body_enabled_switch.value

    @body_enabled.setter
    def body_enabled(self, value: bool) -> None:
        self.body_enabled_switch.value = value

    @property
    def body_mode(self) -> BodyMode:
        return self.body_mode_select.value

    @body_mode.setter
    def body_mode(self, value: BodyMode) -> None:
        self.body_mode_select.value = value

    @property
    def body_raw_language(self) -> BodyRawLanguage:
        return self.body_raw_language_select.value

    @body_raw_language.setter
    def body_raw_language(self, value: BodyRawLanguage) -> None:
        self.body_raw_language_select.value = value

    @property
    def body_raw(self) -> str:
        return self.body_raw_editor.text

    @body_raw.setter
    def body_raw(self, value: str) -> None:
        self.body_raw_editor.text = value

    @property
    def body_file(self) -> Path | None:
        return self.body_file_path_chooser.path

    @body_file.setter
    def body_file(self, value: Path | None) -> None:
        self.body_file_path_chooser.path = value

    @property
    def body_form_urlencoded(self) -> list[dict[str, str | bool]]:
        return [
            {
                'enabled': field.enabled,
                'key': field.key,
                'value': field.value,
            }
            for field in self.body_form_urlencoded_fields.fields
            if field.is_filled or field.enabled
        ]

    @body_form_urlencoded.setter
    def body_form_urlencoded(
        self, values: list[dict[str, str | bool]]
    ) -> None:
        for field in self.body_form_urlencoded_fields.fields:
            self.body_form_urlencoded_fields.remove_field(field=field)

        for value in values:
            self.run_worker(
                self.body_form_urlencoded_fields.add_field(
                    field=TextDynamicField(
                        enabled=value['enabled'],
                        key=value['key'],
                        value=value['value'],
                    ),
                    before_last=True,
                )
            )

    @property
    def body_form_multipart(self) -> list[dict[str, str | bool, Path | None]]:
        return [
            {
                'enabled': field.enabled,
                'key': field.key,
                'value': field.value,
                'value_kind': field.value_kind,
            }
            for field in self.body_form_multipart_fields.fields
            if field.is_filled or field.enabled
        ]

    @body_form_multipart.setter
    def body_form_multipart(
        self, values: list[dict[str, str | bool, Path | None]]
    ) -> None:
        for field in self.body_form_multipart_fields.fields:
            self.body_form_multipart_fields.remove_field(field=field)

        for value in values:
            self.run_worker(
                self.body_form_multipart_fields.add_field(
                    TextOrFileDynamicField(
                        enabled=value['enabled'],
                        key=value['key'],
                        value=value['value'],
                        value_kind=value['value_kind'],
                    ),
                    before_last=True,
                )
            )

    @property
    def option_timeout(self) -> float | None:
        try:
            return float(self.options_timeout_input.value)
        except ValueError:
            return None

    @option_timeout.setter
    def option_timeout(self, value: float | None) -> None:
        self.options_timeout_input.value = '' if value is None else str(value)

    @property
    def option_follow_redirects(self) -> bool:
        return self.options_follow_redirects_switch.value

    @option_follow_redirects.setter
    def option_follow_redirects(self, value: bool) -> None:
        self.options_follow_redirects_switch.value = value

    @property
    def option_verify_ssl(self) -> bool:
        return self.options_verify_ssl_switch.value

    @option_verify_ssl.setter
    def option_verify_ssl(self, value: bool) -> None:
        self.options_verify_ssl_switch.value = value

    def clear(self) -> None:
        self.headers = []
        self.params = []

        self.auth_enabled = False
        self.auth_mode = AuthMode.BASIC
        self.auth_basic_username = ''
        self.auth_basic_password = ''
        self.auth_bearer_token = ''
        self.auth_api_key_key = ''
        self.auth_api_key_value = ''
        self.auth_api_key_where = 'header'
        self.auth_digest_username = ''
        self.auth_digest_password = ''

        self.body_enabled = False
        self.body_mode = BodyMode.RAW
        self.body_raw_language = BodyRawLanguage.PLAIN
        self.body_raw = ''
        self.body_file = None
        self.body_form_urlencoded = []
        self.body_form_multipart = []

        self.option_timeout = None
        self.option_follow_redirects = False
        self.option_verify_ssl = False

    @on(Select.Changed, '#auth-mode')
    def _on_change_auth_mode(self, message: Select.Changed) -> None:
        if message.value == 'basic':
            self.auth_mode_switcher.current = 'auth-basic'
        elif message.value == 'bearer':
            self.auth_mode_switcher.current = 'auth-bearer'
        elif message.value == 'api_key':
            self.auth_mode_switcher.current = 'auth-api-key'
        elif message.value == 'digest':
            self.auth_mode_switcher.current = 'auth-digest'

    @on(Select.Changed, '#body-mode')
    def _on_change_body_mode(self, message: Select.Changed) -> None:
        if message.value == BodyMode.FILE:
            self.body_mode_switcher.current = 'body-mode-file'
        elif message.value == BodyMode.RAW:
            self.body_mode_switcher.current = 'body-mode-raw'
        elif message.value == BodyMode.FORM_URLENCODED:
            self.body_mode_switcher.current = 'body-mode-form-urlencoded'
        elif message.value == BodyMode.FORM_MULTIPART:
            self.body_mode_switcher.current = 'body-mode-form-multipart'

    @on(Select.Changed, '#body-raw-language')
    def _on_change_body_raw_language(self, message: Select.Changed) -> None:
        self.body_raw_editor.language = message.value
