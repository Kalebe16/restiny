from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    ContentSwitcher,
    Input,
    Label,
    Select,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

from restiny.enums import AuthMode, BodyMode, BodyRawLanguage
from restiny.widgets import (
    CustomTextArea,
    DynamicFields,
    PasswordInput,
    PathChooser,
    TextDynamicField,
)
from restiny.widgets.dynamic_fields import TextOrFileDynamicField


@dataclass
class HeaderField:
    enabled: bool
    key: str
    value: str


@dataclass
class ParamField:
    enabled: bool
    key: str
    value: str


@dataclass
class FormUrlEncodedField:
    enabled: bool
    key: str
    value: str


@dataclass
class FormMultipartField:
    enabled: bool
    key: str
    value: str | Path


@dataclass
class BasicAuth:
    username: str
    password: str


@dataclass
class BearerAuth:
    token: str


@dataclass
class APIKeyAuth:
    key: str
    value: str
    where: Literal['header', 'param']


@dataclass
class DigestAuth:
    username: str
    password: str


@dataclass
class Options:
    timeout: int | float | None
    follow_redirects: bool
    verify_ssl: bool


@dataclass
class Body:
    enabled: bool
    raw_language: BodyRawLanguage | None
    mode: BodyMode
    payload: (
        str
        | Path
        | list[FormUrlEncodedField]
        | list[FormMultipartField]
        | None
    )


_AuthType = BasicAuth | BearerAuth | APIKeyAuth | DigestAuth


@dataclass
class Auth:
    enabled: bool
    value: _AuthType


@dataclass
class RequestAreaData:
    headers: list[HeaderField]
    params: list[ParamField]
    auth: Auth
    body: Body
    options: Options


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
                        yield Input(
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
                        yield Input(
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
                        yield Input(
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
                    yield Input(
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
            '#auth-basic-username', Input
        )
        self.auth_basic_password_input = self.query_one(
            '#auth-basic-password', PasswordInput
        )
        self.auth_bearer_token_input = self.query_one(
            '#auth-bearer-token', PasswordInput
        )
        self.auth_api_key_key_input = self.query_one(
            '#auth-api-key-key', Input
        )
        self.auth_api_key_value_input = self.query_one(
            '#auth-api-key-value', PasswordInput
        )
        self.auth_api_key_where_select = self.query_one(
            '#auth-api-key-where', Select
        )
        self.auth_digest_username_input = self.query_one(
            '#auth-digest-username', Input
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

        self.options_timeout_input = self.query_one('#options-timeout', Input)
        self.options_follow_redirects_switch = self.query_one(
            '#options-follow-redirects', Switch
        )
        self.options_verify_ssl_switch = self.query_one(
            '#options-verify-ssl', Switch
        )

    def get_data(self) -> RequestAreaData:
        return RequestAreaData(
            headers=self._get_headers(),
            params=self._get_params(),
            auth=self._get_auth(),
            body=self._get_body(),
            options=self._get_options(),
        )

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

    @on(DynamicFields.FieldFilled, '#body-form-urlencoded')
    def _on_form_filled(self, message: DynamicFields.FieldFilled) -> None:
        self.body_enabled_switch.value = True

    @on(DynamicFields.FieldEmpty, '#body-form-urlencoded')
    def _on_form_empty(self, message: DynamicFields.FieldEmpty) -> None:
        if not message.control.filled_fields:
            self.body_enabled_switch.value = False

    @on(CustomTextArea.Changed, '#body-raw')
    def _on_change_body_raw(self, message: CustomTextArea.Changed) -> None:
        if self.body_raw_editor.text == '':
            self.body_enabled_switch.value = False
        else:
            self.body_enabled_switch.value = True

    def _get_headers(self) -> list[HeaderField]:
        return [
            HeaderField(
                enabled=header_field['enabled'],
                key=header_field['key'],
                value=header_field['value'],
            )
            for header_field in self.header_fields.values
        ]

    def _get_params(self) -> list[ParamField]:
        return [
            ParamField(
                enabled=param_field['enabled'],
                key=param_field['key'],
                value=param_field['value'],
            )
            for param_field in self.param_fields.values
        ]

    def _get_auth(self) -> _AuthType:
        if self.auth_mode_select.value == AuthMode.BASIC:
            return Auth(
                enabled=self.auth_enabled_switch.value,
                value=BasicAuth(
                    username=self.auth_basic_username_input.value,
                    password=self.auth_basic_password_input.value,
                ),
            )
        elif self.auth_mode_select.value == AuthMode.BEARER:
            return Auth(
                enabled=self.auth_enabled_switch.value,
                value=BearerAuth(token=self.auth_bearer_token_input.value),
            )
        elif self.auth_mode_select.value == AuthMode.API_KEY:
            return Auth(
                enabled=self.auth_enabled_switch.value,
                value=APIKeyAuth(
                    key=self.auth_api_key_key_input.value,
                    value=self.auth_api_key_value_input.value,
                    where=self.auth_api_key_where_select.value,
                ),
            )
        elif self.auth_mode_select.value == AuthMode.DIGEST:
            return Auth(
                enabled=self.auth_enabled_switch.value,
                value=DigestAuth(
                    username=self.auth_digest_username_input.value,
                    password=self.auth_digest_password_input.value,
                ),
            )

    def _get_body(self) -> Body:
        body_send: bool = self.body_enabled_switch.value
        body_mode: str = BodyMode(self.body_mode_select.value)

        payload = None
        if body_mode == BodyMode.RAW:
            payload = self.body_raw_editor.text
        elif body_mode == BodyMode.FILE:
            payload = self.body_file_path_chooser.path
        elif body_mode == BodyMode.FORM_URLENCODED:
            payload = []
            for form_item in self.body_form_urlencoded_fields.values:
                payload.append(
                    FormUrlEncodedField(
                        enabled=form_item['enabled'],
                        key=form_item['key'],
                        value=form_item['value'],
                    )
                )
        elif body_mode == BodyMode.FORM_MULTIPART:
            payload = []
            for form_item in self.body_form_multipart_fields.values:
                payload.append(
                    FormMultipartField(
                        enabled=form_item['enabled'],
                        key=form_item['key'],
                        value=form_item['value'],
                    )
                )

        return Body(
            enabled=body_send,
            raw_language=BodyRawLanguage(self.body_raw_language_select.value),
            mode=body_mode,
            payload=payload,
        )

    def _get_options(self) -> Options:
        try:
            timeout = float(self.options_timeout_input.value)
        except ValueError:
            timeout = None

        return Options(
            timeout=timeout,
            follow_redirects=self.options_follow_redirects_switch.value,
            verify_ssl=self.options_verify_ssl_switch.value,
        )
