from dataclasses import dataclass
from pathlib import Path

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

from restiny.enums import BodyMode, BodyRawLanguage
from restiny.widgets import (
    CustomTextArea,
    DynamicFields,
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
class QueryParamField:
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
class RequestAreaData:
    @dataclass
    class Options:
        timeout: int | float | None
        follow_redirects: bool
        verify_ssl: bool

    @dataclass
    class Body:
        enabled: bool
        raw_language: BodyRawLanguage | None
        type: BodyMode
        payload: (
            str
            | Path
            | list[FormUrlEncodedField]
            | list[FormMultipartField]
            | None
        )

    headers: list[HeaderField]
    query_params: list[QueryParamField]
    body: Body
    options: Options


class RequestArea(Static):
    ALLOW_MAXIMIZE = True
    can_focus = True
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
            with TabPane('Query params'):
                yield DynamicFields(
                    fields=[TextDynamicField(enabled=False, key='', value='')],
                    id='params',
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
                        tooltip='Body type',
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
                        id='options-timeout',
                        classes='w-1fr',
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

    @on(Select.Changed, '#body-mode')
    def on_change_body_type(self, message: Select.Changed) -> None:
        if message.value == BodyMode.FILE:
            self.body_mode_switcher.current = 'body-mode-file'
        elif message.value == BodyMode.RAW:
            self.body_mode_switcher.current = 'body-mode-raw'
        elif message.value == BodyMode.FORM_URLENCODED:
            self.body_mode_switcher.current = 'body-mode-form-urlencoded'
        elif message.value == BodyMode.FORM_MULTIPART:
            self.body_mode_switcher.current = 'body-mode-form-multipart'

    @on(Select.Changed, '#body-raw-language')
    def on_change_body_text_language(self, message: Select.Changed) -> None:
        self.body_raw_editor.language = message.value

    @on(DynamicFields.FieldFilled, '#body-form-urlencoded')
    def on_form_filled(self, message: DynamicFields.FieldFilled) -> None:
        self.body_enabled_switch.value = True

    @on(DynamicFields.FieldEmpty, '#body-form-urlencoded')
    def on_form_empty(self, message: DynamicFields.FieldEmpty) -> None:
        if not message.control.filled_fields:
            self.body_enabled_switch.value = False

    @on(CustomTextArea.Changed, '#body-raw')
    def on_change_body_text(self, message: CustomTextArea.Changed) -> None:
        if self.body_raw_editor.text == '':
            self.body_enabled_switch.value = False
        else:
            self.body_enabled_switch.value = True

    @on(Input.Changed, '#options-timeout')
    def on_change_timeout(self, message: Input.Changed) -> None:
        new_value = message.value

        if new_value == '':
            return

        try:
            float(new_value)
        except Exception:
            self.options_timeout_input.value = (
                self.options_timeout_input.value[:-1]
            )

    def get_data(self) -> RequestAreaData:
        def get_headers() -> list[HeaderField]:
            return [
                HeaderField(
                    enabled=header_field['enabled'],
                    key=header_field['key'],
                    value=header_field['value'],
                )
                for header_field in self.header_fields.values
            ]

        def get_query_params() -> list[QueryParamField]:
            return [
                QueryParamField(
                    enabled=query_param_field['enabled'],
                    key=query_param_field['key'],
                    value=query_param_field['value'],
                )
                for query_param_field in self.param_fields.values
            ]

        def get_body() -> RequestAreaData.Body:
            body_send: bool = self.body_enabled_switch.value
            body_type: str = BodyMode(self.body_mode_select.value)

            payload = None
            if body_type == BodyMode.RAW:
                payload = self.body_raw_editor.text
            elif body_type == BodyMode.FILE:
                payload = self.body_file_path_chooser.path
            elif body_type == BodyMode.FORM_URLENCODED:
                payload = []
                for form_item in self.body_form_urlencoded_fields.values:
                    payload.append(
                        FormUrlEncodedField(
                            enabled=form_item['enabled'],
                            key=form_item['key'],
                            value=form_item['value'],
                        )
                    )
            elif body_type == BodyMode.FORM_MULTIPART:
                payload = []
                for form_item in self.body_form_multipart_fields.values:
                    payload.append(
                        FormMultipartField(
                            enabled=form_item['enabled'],
                            key=form_item['key'],
                            value=form_item['value'],
                        )
                    )

            return RequestAreaData.Body(
                enabled=body_send,
                raw_language=BodyRawLanguage(
                    self.body_raw_language_select.value
                ),
                type=body_type,
                payload=payload,
            )

        def get_options() -> RequestAreaData.Options:
            timeout = None
            if self.options_timeout_input.value:
                timeout = float(self.options_timeout_input.value)

            return RequestAreaData.Options(
                timeout=timeout,
                follow_redirects=self.options_follow_redirects_switch.value,
                verify_ssl=self.options_verify_ssl_switch.value,
            )

        return RequestAreaData(
            headers=get_headers(),
            query_params=get_query_params(),
            body=get_body(),
            options=get_options(),
        )
