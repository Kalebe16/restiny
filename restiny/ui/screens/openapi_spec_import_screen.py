from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button

from restiny.entities import Folder, Request
from restiny.enums import BodyMode, BodyRawLanguage, HTTPMethod
from restiny.logger import get_logger
from restiny.widgets import PathChooser

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


logger = get_logger()


class _ImportFailedError(Exception):
    pass


class _ImportInvalidFileError(Exception):
    pass


class _ImportInvalidVersionError(Exception):
    pass


class OpenapiSpecImportScreen(ModalScreen):
    app: RESTinyApp

    DEFAULT_CSS = """
    OpenapiSpecImportScreen {
        align: center middle;
    }

    #modal-content {
        width: 30%;
        height: auto;
        border: heavy $panel;
        border-title-color: $text-muted;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding(
            key='escape',
            action='dismiss',
            description='Quit the screen',
            show=False,
        ),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-content'):
            with Horizontal(classes='w-auto h-auto p-1'):
                yield PathChooser.file(
                    id='open-api-spec-file',
                    allowed_file_suffixes=['.json', '.yaml', '.yml'],
                )
            with Horizontal(classes='w-auto h-auto'):
                yield Button('Cancel', classes='w-1fr', id='cancel')
                yield Button('Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)

        self.openapi_spec_file_chooser = self.query_one(
            '#open-api-spec-file', PathChooser
        )
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Openapi spec import'

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self) -> None:
        self.dismiss(result=False)

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self) -> None:
        if not self.openapi_spec_file_chooser.path:
            self.notify('Openapi spec file is required', severity='error')
            return

        try:
            self._import()
        except _ImportInvalidFileError:
            self.notify('Invalid openapi spec file', severity='error')
            return
        except _ImportInvalidVersionError:
            self.notify("Only '2.0' and '3.0' is supported")
        except _ImportFailedError:
            self.notify('Failed to import the openapi spec', severity='error')
            return
        except Exception:
            self.notify(
                'Failed to import the openapi spec; unexpected error',
                severity='error',
            )
            logger.exception('Failed to import the openapi spec')
            return

        self.notify(message='Openapi spec imported', severity='information')
        self.dismiss(result=True)

    def _import(self) -> None:
        self.spec, spec_version = self._load_spec(
            spec_file=self.openapi_spec_file_chooser.path
        )

        if '2.0' in spec_version:
            self._import_v2_0()
        elif '3.0' in spec_version:
            self._import_v3_0()
        else:
            raise _ImportInvalidVersionError()

    def _load_spec(self, spec_file: Path) -> tuple[dict, str]:
        try:
            raw_text = spec_file.read_text()
        except OSError as exc:
            raise _ImportInvalidFileError() from exc

        if spec_file.suffix == '.json':
            try:
                spec = json.loads(raw_text)
            except json.JSONDecodeError as error:
                raise _ImportInvalidFileError() from error

            if not isinstance(spec, dict):
                raise _ImportInvalidFileError()
        elif spec_file.suffix in ('.yaml', '.yml'):
            try:
                spec = yaml.load(raw_text)
            except yaml.YAMLError as error:
                raise _ImportInvalidFileError() from error

            if not isinstance(spec, dict):
                raise _ImportInvalidFileError()
        else:
            raise _ImportInvalidFileError()

        spec_version = spec.get('swagger') or spec.get('openapi')
        if not isinstance(spec_version, str):
            raise _ImportInvalidVersionError()

        return spec, spec_version

    def _import_v2_0(self) -> None:
        with self.app.db_manager.session_scope() as session:
            # Create root folder
            create_resp = self.app.folders_repo.create(
                session=session,
                folder=Folder(parent_id=None, name=self.spec['info']['title']),
            )
            if not create_resp.ok:
                raise _ImportFailedError()
            root_folder = create_resp.data

            # Create sub folders
            tag_name_to_folder: dict[str, Folder] = {}
            for tag in self.spec['tags']:
                create_resp = self.app.folders_repo.create(
                    session=session,
                    folder=Folder(parent_id=root_folder.id, name=tag['name']),
                )
                if not create_resp.ok:
                    raise _ImportFailedError()
                folder = create_resp.data
                tag_name_to_folder[tag['name']] = folder

            # Create requests
            scheme = 'http'
            if 'https' in self.spec.get('schemes', []):
                scheme = 'https'
            host = self.spec.get('host', 'localhost')
            base_path = self.spec.get('basePath', '')
            base_url = f'{scheme}://{host}{base_path}'

            for path, methods in self.spec['paths'].items():
                url = base_url + path

                for method, operation in methods.items():
                    form_data_kind: (
                        Literal['urlencoded', 'multipart'] | None
                    ) = None
                    if all(
                        parameter.get('type') == 'string'
                        for parameter in operation.get('parameters', [])
                        if parameter.get('in') == 'formData'
                    ):
                        form_data_kind = 'urlencoded'
                    elif any(
                        parameter.get('type') == 'file'
                        for parameter in operation.get('parameters', [])
                        if parameter.get('in') == 'formData'
                    ):
                        form_data_kind = 'multipart'

                    headers: list[Request.Header] = []
                    params: list[Request.Param] = []
                    form_data_fields: list[
                        Request.MultipartFormBody.Field
                        | Request.UrlEncodedFormBody.Field
                    ] = []
                    body_enabled = False
                    body_mode = BodyMode.RAW
                    body = None

                    for parameter in operation.get('parameters', []):
                        if parameter['in'] == 'header':
                            headers.append(
                                Request.Header(
                                    enabled=False,
                                    key=parameter['name'],
                                    value='',
                                )
                            )
                        elif parameter['in'] == 'query':
                            params.append(
                                Request.Param(
                                    enabled=False,
                                    key=parameter['name'],
                                    value='',
                                )
                            )
                        elif parameter['in'] == 'formData':
                            if form_data_kind == 'urlencoded':
                                body_mode = BodyMode.FORM_URLENCODED
                                form_data_fields.append(
                                    Request.UrlEncodedFormBody.Field(
                                        enabled=False,
                                        key=parameter['name'],
                                        value='',
                                    )
                                )
                            elif form_data_kind == 'multipart':
                                body_mode = BodyMode.FORM_MULTIPART
                                form_data_fields.append(
                                    Request.MultipartFormBody.Field(
                                        enabled=False,
                                        key=parameter['name'],
                                        value=''
                                        if parameter['type'] == 'string'
                                        else None,
                                        value_kind='text'
                                        if parameter['type'] == 'string'
                                        else 'file',
                                    )
                                )
                        elif parameter['in'] == 'body':
                            body_mode = BodyMode.RAW
                            body = Request.RawBody(
                                language=BodyRawLanguage.JSON,
                                value=json.dumps(
                                    self._build_json_body_from_schema(
                                        schema=self._resolve_schema_ref(
                                            schema=parameter['schema'],
                                        ),
                                    ),
                                    indent=4,
                                ),
                            )

                    if body_mode == BodyMode.FORM_URLENCODED:
                        body = Request.UrlEncodedFormBody(
                            fields=form_data_fields
                        )
                    elif body_mode == BodyMode.FORM_MULTIPART:
                        body = Request.MultipartFormBody(
                            fields=form_data_fields
                        )

                    folder_id = root_folder.id
                    if operation.get('tags'):
                        folder_id = tag_name_to_folder.get(
                            operation['tags'][0], root_folder
                        ).id
                    create_req_resp = self.app.requests_repo.create(
                        session=session,
                        request=Request(
                            folder_id=folder_id,
                            name=operation.get('operationId')
                            or operation.get('summary')
                            or path.lstrip('/'),
                            method=HTTPMethod(method.upper()),
                            url=url,
                            headers=headers,
                            params=params,
                            body_enabled=body_enabled,
                            body_mode=body_mode,
                            body=body,
                        ),
                    )
                    if not create_req_resp.ok:
                        raise _ImportFailedError()

    def _import_v3_0(self) -> None:
        with self.app.db_manager.session_scope() as session:
            # Create root folder
            create_resp = self.app.folders_repo.create(
                session=session,
                folder=Folder(parent_id=None, name=self.spec['info']['title']),
            )
            if not create_resp.ok:
                raise _ImportFailedError()
            root_folder = create_resp.data

            # Create sub folders
            tag_name_to_folder: dict[str, Folder] = {}
            for tag in self.spec['tags']:
                create_resp = self.app.folders_repo.create(
                    session=session,
                    folder=Folder(parent_id=root_folder.id, name=tag['name']),
                )
                if not create_resp.ok:
                    raise _ImportFailedError()
                folder = create_resp.data
                tag_name_to_folder[tag['name']] = folder

            # Create requests
            base_url = f'{self.spec["servers"][0]["url"]}'
            if not base_url.startswith('http'):
                base_url = '{{BASE_URL}}' + base_url

            for path, methods in self.spec['paths'].items():
                url = base_url + path

                for method, operation in methods.items():
                    headers: list[Request.Header] = []
                    params: list[Request.Param] = []
                    body_enabled = False
                    body_mode = BodyMode.RAW
                    body = None

                    for parameter in operation.get('parameters', []):
                        if parameter.get('in') == 'header':
                            headers.append(
                                Request.Header(
                                    enabled=False,
                                    key=parameter['name'],
                                    value='',
                                )
                            )
                        elif parameter.get('in') == 'query':
                            params.append(
                                Request.Param(
                                    enabled=False,
                                    key=parameter['name'],
                                    value='',
                                )
                            )

                    request_body = operation.get('requestBody')
                    if request_body:
                        content = self._resolve_schema_ref(
                            schema=request_body
                        ).get('content', {})
                        json_body = content.get('application/json')
                        urlencoded_form_body = content.get(
                            'application/x-www-form-urlencoded'
                        )
                        multipart_form_body = content.get(
                            'multipart/form-data'
                        )
                        file_body = content.get('application/octet-stream')
                        if json_body:
                            body_schema = self._resolve_schema_ref(
                                schema=json_body
                            )
                            body_schema = body_schema.get(
                                'schema', body_schema
                            )
                            body_schema = self._resolve_schema_ref(
                                schema=body_schema
                            )

                            body_mode = BodyMode.RAW
                            body = Request.RawBody(
                                language=BodyRawLanguage.JSON,
                                value=json.dumps(
                                    self._build_json_body_from_schema(
                                        schema=body_schema
                                    ),
                                    indent=4,
                                ),
                            )
                        elif urlencoded_form_body:
                            body_schema = self._resolve_schema_ref(
                                schema=urlencoded_form_body
                            )
                            body_schema = body_schema.get(
                                'schema', body_schema
                            )
                            body_schema = self._resolve_schema_ref(
                                schema=body_schema
                            )

                            body_mode = BodyMode.FORM_URLENCODED
                            body = Request.UrlEncodedFormBody(
                                fields=[
                                    Request.UrlEncodedFormBody.Field(
                                        enabled=False,
                                        key=prop_key,
                                        value=str(prop.get('example', '')),
                                    )
                                    for prop_key, prop in body_schema[
                                        'properties'
                                    ].items()
                                ]
                            )
                        elif multipart_form_body:
                            body_schema = self._resolve_schema_ref(
                                schema=multipart_form_body
                            )
                            body_schema = body_schema.get(
                                'schema', body_schema
                            )
                            body_schema = self._resolve_schema_ref(
                                schema=body_schema
                            )

                            body_mode = BodyMode.FORM_MULTIPART
                            body = Request.MultipartFormBody(
                                fields=[
                                    Request.MultipartFormBody.Field(
                                        enabled=False,
                                        key=prop_key,
                                        value=None
                                        if prop.get('format') == 'binary'
                                        else '',
                                        value_kind='file'
                                        if prop.get('format') == 'binary'
                                        else 'text',
                                    )
                                    for prop_key, prop in body_schema[
                                        'properties'
                                    ].items()
                                ]
                            )
                        elif file_body:
                            body_mode = BodyMode.FILE

                    folder_id = root_folder.id
                    if operation.get('tags'):
                        folder_id = tag_name_to_folder.get(
                            operation['tags'][0], root_folder
                        ).id
                    create_req_resp = self.app.requests_repo.create(
                        session=session,
                        request=Request(
                            folder_id=folder_id,
                            name=operation.get('operationId')
                            or operation.get('summary')
                            or path.lstrip('/'),
                            method=HTTPMethod(method.upper()),
                            url=url,
                            headers=headers,
                            params=params,
                            body_enabled=body_enabled,
                            body_mode=body_mode,
                            body=body,
                        ),
                    )
                    if not create_req_resp.ok:
                        raise _ImportFailedError()

    def _resolve_schema_ref(self, schema: dict) -> dict:
        ref = schema.get('$ref')
        if not ref:
            return schema

        # OpenAPI 2.0
        if ref.startswith('#/definitions/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['definitions'][schema_name]
        if ref.startswith('#/parameters/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['parameters'][schema_name]
        if ref.startswith('#/responses/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['responses'][schema_name]

        # OpenAPI 3.0
        if ref.startswith('#/components/schemas/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['components']['schemas'][schema_name]
        if ref.startswith('#/components/parameters/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['components']['parameters'][schema_name]
        if ref.startswith('#/components/responses/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['components']['responses'][schema_name]
        if ref.startswith('#/components/requestBodies/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['components']['requestBodies'][schema_name]

        return schema

    def _build_json_body_from_schema(self, schema: dict) -> Any:
        schema = self._resolve_schema_ref(schema=schema)

        if 'example' in schema:
            return schema['example']
        if 'default' in schema:
            return schema['default']

        schema_type = schema.get('type')
        if schema_type == 'object':
            props = schema.get('properties', {})
            obj = {}
            for prop_name, prop in props.items():
                obj[prop_name] = self._build_json_body_from_schema(schema=prop)
            return obj
        elif schema_type == 'array':
            items = schema.get('items', {})
            return [self._build_json_body_from_schema(schema=items)]
        elif schema_type == 'integer':
            return 0
        elif schema_type == 'number':
            return 0.0
        elif schema_type == 'boolean':
            return False
        elif schema_type == 'string':
            fmt = schema.get('format')
            if fmt == 'date-time':
                return datetime.now(UTC).isoformat()
            elif fmt == 'date':
                return date.today().isoformat()
            elif fmt == 'uuid':
                return '00000000-0000-0000-0000-000000000000'
            return ''

        return {}
