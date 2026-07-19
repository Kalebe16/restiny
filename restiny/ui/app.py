import json
import webbrowser
from datetime import UTC, date, datetime
from http import HTTPMethod
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

import httpx
import yaml
from packaging import version
from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
    model_validator,
)
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QToolButton,
    QWidget,
)

from restiny.__about__ import __version__
from restiny.assets import (
    APP_ICON,
    COLLECTIONS_ICON,
    ENVIRONMENTS_ICON,
    SETTINGS_ICON,
)
from restiny.data.db import DBManager
from restiny.data.repos import (
    EnvironmentsSQLRepo,
    FoldersSQLRepo,
    RequestsSQLRepo,
    SettingsSQLRepo,
)
from restiny.entities import Environment, Folder, Request
from restiny.enums import AuthMode, BodyMode, BodyRawLanguage
from restiny.ui.collections_screen import CollectionsScreen
from restiny.ui.environments_screen import EnvironmentScreen
from restiny.ui.settings_screen import SettingsScreen


class _ImportInvalidVersionError(Exception):
    pass


class _ImportFailedError(Exception):
    pass


class _ImportInvalidFileError(Exception):
    pass


class ExportedEnvironment(BaseModel):
    class ExportedVariable(BaseModel):
        enabled: bool
        key: str
        value: str

    name: str
    variables: list[ExportedVariable] = []

    def to_domain(self) -> Environment:
        return Environment(
            id=None,
            name=self.name,
            variables=[
                Environment.Variable(
                    enabled=v.enabled, key=v.key, value=v.value
                )
                for v in self.variables
            ],
            created_at=None,
            updated_at=None,
        )


class ExportedEnvironmentFileV1(BaseModel):
    format: str
    version: int
    environment: ExportedEnvironment

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v != 'restiny-environment':
            raise ValueError("format must be 'restiny-environment'")
        return v

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: int) -> int:
        if v != 1:
            raise ValueError('version must be 1')
        return v


class ExportedFolder(BaseModel):
    uuid: UUID
    parent_uuid: UUID | None = None
    name: str

    def to_domain(self, folder_id: int) -> Folder:
        return Folder(
            parent_id=folder_id,
            name=self.name,
            uuid=self.uuid,
        )


class ExportedRequest(BaseModel):
    class ExportedHeader(BaseModel):
        enabled: bool
        key: str
        value: str

    class ExportedParam(BaseModel):
        enabled: bool
        key: str
        value: str

    class RawBody(BaseModel):
        language: BodyRawLanguage
        value: str | dict | list

        @model_validator(mode='after')
        def validate_value(self):
            if self.language == BodyRawLanguage.JSON and not isinstance(
                self.value, (dict, list)
            ):
                raise ValueError('JSON body must be dict or list')
            if self.language != BodyRawLanguage.JSON and not isinstance(
                self.value, str
            ):
                raise ValueError('Non-JSON body must be string')
            return self

    class FileBody(BaseModel):
        file: str | None

    class UrlEncodedFormBody(BaseModel):
        class Field(BaseModel):
            enabled: bool
            key: str
            value: str

        fields: list[Field]

    class MultipartFormBody(BaseModel):
        class Field(BaseModel):
            value_kind: Literal['text', 'file']
            enabled: bool
            key: str
            value: str | None

        fields: list[Field]

    class BasicAuth(BaseModel):
        username: str
        password: str

    class BearerAuth(BaseModel):
        token: str

    class ApiKeyAuth(BaseModel):
        key: str
        value: str
        where: Literal['header', 'param']

    class DigestAuth(BaseModel):
        username: str
        password: str

    class Options(BaseModel):
        timeout: float = 5.5
        follow_redirects: bool = True
        verify_ssl: bool = True
        attach_cookies: bool = True

    uuid: UUID
    folder_uuid: UUID
    name: str
    method: HTTPMethod
    url: str
    headers: list[ExportedHeader] = []
    params: list[ExportedParam] = []

    body_enabled: bool = False
    body_mode: BodyMode = BodyMode.RAW
    body: RawBody | FileBody | UrlEncodedFormBody | MultipartFormBody = (
        RawBody(language=BodyRawLanguage.PLAIN, value='')
    )

    auth_enabled: bool = False
    auth_mode: AuthMode = AuthMode.BASIC
    auth: BasicAuth | BearerAuth | ApiKeyAuth | DigestAuth = BasicAuth(
        username='', password=''
    )

    options: Options = Options()

    def to_domain(self, folder_id: int) -> Request:
        if isinstance(self.body, ExportedRequest.RawBody):
            body = Request.RawBody(
                language=self.body.language,
                value=(
                    json.dumps(self.body.value, ensure_ascii=False, indent=2)
                    if self.body.language == BodyRawLanguage.JSON
                    else str(self.body.value)
                ),
            )
        elif isinstance(self.body, ExportedRequest.FileBody):
            body = Request.FileBody(
                file=Path(self.body.file) if self.body.file else None
            )
        elif isinstance(self.body, ExportedRequest.UrlEncodedFormBody):
            body = Request.UrlEncodedFormBody(
                fields=[
                    Request.UrlEncodedFormBody.Field(**f.model_dump())
                    for f in self.body.fields
                ]
            )
        elif isinstance(self.body, ExportedRequest.MultipartFormBody):
            body = Request.MultipartFormBody(
                fields=[
                    Request.MultipartFormBody.Field(**f.model_dump())
                    for f in self.body.fields
                ]
            )
        else:
            body = Request.RawBody(language=BodyRawLanguage.PLAIN, value='')

        if isinstance(self.auth, ExportedRequest.BasicAuth):
            auth = Request.BasicAuth(**self.auth.model_dump())
        elif isinstance(self.auth, ExportedRequest.BearerAuth):
            auth = Request.BearerAuth(**self.auth.model_dump())
        elif isinstance(self.auth, ExportedRequest.ApiKeyAuth):
            auth = Request.ApiKeyAuth(**self.auth.model_dump())
        elif isinstance(self.auth, ExportedRequest.DigestAuth):
            auth = Request.DigestAuth(**self.auth.model_dump())
        else:
            auth = Request.BasicAuth(username='', password='')

        return Request(
            folder_id=folder_id,
            name=self.name,
            method=self.method,
            url=self.url,
            headers=[Request.Header(**h.model_dump()) for h in self.headers],
            params=[Request.Param(**p.model_dump()) for p in self.params],
            body_enabled=self.body_enabled,
            body_mode=self.body_mode,
            body=body,
            auth_enabled=self.auth_enabled,
            auth_mode=self.auth_mode,
            auth=auth,
            options=Request.Options(**self.options.model_dump()),
            uuid=self.uuid,
        )


class ExportedCollection(BaseModel):
    uuid: UUID
    name: str
    folders: list[ExportedFolder] = []
    requests: list[ExportedRequest] = []


class ExportedCollectionFileV1(BaseModel):
    format: str
    version: int
    collection: ExportedCollection

    @field_validator('format')
    @classmethod
    def validate_format(cls, value: str) -> str:
        if value != 'restiny-collection':
            raise ValueError("format must be 'restiny-collection'")
        return value

    @field_validator('version')
    @classmethod
    def validate_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError('version must be 1')
        return value


class MainWindow(QMainWindow):
    def __init__(
        self,
        db_manager: DBManager,
        folders_repo: FoldersSQLRepo,
        requests_repo: RequestsSQLRepo,
        environments_repo: EnvironmentsSQLRepo,
        settings_repo: SettingsSQLRepo,
    ) -> None:
        super().__init__()
        self.db_manager = db_manager
        self.folders_repo = folders_repo
        self.requests_repo = requests_repo
        self.environments_repo = environments_repo
        self.settings_repo = settings_repo

        self.setWindowTitle(
            f'RESTiny {__version__} - Minimal HTTP client, no bullshit'
        )
        self.setWindowIcon(QIcon(str(APP_ICON)))
        self.resize(1400, 800)

        toolbar = QToolBar('Main Toolbar')
        import_button = QToolButton()
        import_button.setText('Import')
        import_button.setPopupMode(QToolButton.InstantPopup)
        import_menu = QMenu(import_button)
        import_collection_action = QAction('Import collection', self)
        import_environment_action = QAction('Import environment', self)
        import_open_api_spec_action = QAction('Import openapi spec', self)
        import_postman_collection_action = QAction(
            'Import postman collection', self
        )
        import_postman_environment_action = QAction(
            'Import postman environment', self
        )
        import_collection_action.triggered.connect(self._on_import_collection)
        import_environment_action.triggered.connect(
            self._on_import_environment
        )
        import_open_api_spec_action.triggered.connect(
            self._on_import_open_api_spec
        )
        import_postman_collection_action.triggered.connect(
            self._on_import_postman_collection
        )
        import_postman_environment_action.triggered.connect(
            self._on_import_postman_environment
        )
        import_menu.addAction(import_collection_action)
        import_menu.addAction(import_environment_action)
        import_menu.addAction(import_open_api_spec_action)
        import_menu.addAction(import_postman_collection_action)
        import_menu.addAction(import_postman_environment_action)
        import_button.setMenu(import_menu)
        export_button = QToolButton()
        export_button.setText('Export')
        export_button.setPopupMode(QToolButton.InstantPopup)
        export_menu = QMenu(export_button)
        export_collection_action = QAction('Export collection', self)
        export_environment_action = QAction('Export environment', self)
        export_request_as_curl_action = QAction('Export request as cURL', self)
        export_collection_action.triggered.connect(self._on_export_collection)
        export_environment_action.triggered.connect(
            self._on_export_environment
        )
        export_request_as_curl_action.triggered.connect(
            self._on_export_request_as_curl
        )
        export_menu.addAction(export_collection_action)
        export_menu.addAction(export_environment_action)
        export_menu.addAction(export_request_as_curl_action)
        export_button.setMenu(export_menu)
        toolbar.addWidget(import_button)
        toolbar.addWidget(export_button)
        self.addToolBar(toolbar)

        sidebar = QToolBar('Sidebar')
        sidebar.setIconSize(QSize(32, 32))
        sidebar.setMovable(False)
        collections_action = QAction(
            QIcon(str(COLLECTIONS_ICON)), 'Collections', self
        )
        environments_action = QAction(
            QIcon(str(ENVIRONMENTS_ICON)), 'Environments', self
        )
        settings_action = QAction(QIcon(str(SETTINGS_ICON)), 'Settings', self)
        collections_action.triggered.connect(self._on_collections_clicked)
        environments_action.triggered.connect(self._on_environments_clicked)
        settings_action.triggered.connect(self._on_settings_clicked)
        sidebar.addAction(collections_action)
        sidebar.addAction(environments_action)
        sidebar.addAction(settings_action)
        self.addToolBar(Qt.LeftToolBarArea, sidebar)

        self.collections_screen = CollectionsScreen(
            main_window=self,
            folders_repo=self.folders_repo,
            requests_repo=self.requests_repo,
            environments_repo=self.environments_repo,
            settings_repo=self.settings_repo,
        )
        self.environments_screen = EnvironmentScreen(
            main_window=self,
            environments_repo=self.environments_repo,
            settings_repo=self.settings_repo,
        )
        self.settings_screen = SettingsScreen(settings_repo=self.settings_repo)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.collections_screen)
        self.stack.addWidget(self.environments_screen)
        self.stack.addWidget(self.settings_screen)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(sidebar, 1)
        layout.addWidget(self.stack, 12)
        self.setCentralWidget(container)

        self.environments_screen.sig_added.connect(
            self.collections_screen.top_bar_area._populate_environments
        )
        self.environments_screen.sig_removed.connect(
            self.collections_screen.top_bar_area._populate_environments
        )
        self.environments_screen.sig_saved.connect(
            self.collections_screen.top_bar_area._populate_environments
        )
        QTimer.singleShot(3000, self._check_new_release)

    def _on_collections_clicked(self) -> None:
        self.stack.setCurrentIndex(0)

    def _on_environments_clicked(self) -> None:
        self.stack.setCurrentIndex(1)

    def _on_settings_clicked(self) -> None:
        self.stack.setCurrentIndex(2)

    def _check_new_release(self) -> None:
        try:
            resp = httpx.get(
                'https://api.github.com/repos/Kalebe16/restiny/releases/latest',
                timeout=10,
            )
            resp.raise_for_status()
            latest_version = resp.json()['tag_name']
            if version.parse(latest_version.replace('v', '')) > version.parse(
                __version__
            ):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle('New release available')
                msg.setText(f'New release: {latest_version}')

                open_btn = QPushButton('Open')
                msg.addButton(open_btn, QMessageBox.AcceptRole)

                if msg.exec_() == QMessageBox.AcceptRole:
                    webbrowser.open(
                        'https://github.com/Kalebe16/restiny/releases'
                    )
        except Exception:
            pass

    def _on_import_open_api_spec(self) -> None:
        file, _ = QFileDialog.getOpenFileName(
            self,
            'Import openapi spec',
            '',
            'JSON files (*.json)',
        )

        if not file:
            return

        file = Path(file)

        try:
            self.spec, spec_version = self._load_openapi_spec(spec_file=file)

            if '2.0' in spec_version:
                self._import_openapi_spec_v2_0()
            elif '3.0' in spec_version:
                self._import_openapi_spec_v3_0()
            else:
                raise _ImportInvalidVersionError()
        except _ImportInvalidFileError:
            QMessageBox.critical(self, 'Error', 'Invalid openapi spec file')
            return
        except _ImportInvalidVersionError:
            QMessageBox.critical(
                self, 'Error', "Only '2.0' and '3.0' is supported"
            )
        except _ImportFailedError:
            QMessageBox.critical(
                self, 'Error', 'Failed to import openapi spec'
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to import openapi spec; unexpected error: {error}',
            )
            return

        QMessageBox.information(
            self,
            'Information',
            'openapi spec imported',
        )

    def _on_import_postman_environment(self) -> None:
        try:
            file, _ = QFileDialog.getOpenFileName(
                self,
                'Import Postman Collection',
                '',
                'JSON files (*.json)',
            )

            if not file:
                return

            file = Path(file)

            try:
                environment = json.loads(file.read_text())
            except Exception as error:
                raise _ImportInvalidFileError() from error

            variables = []
            for variable in environment['values']:
                variables.append(
                    Environment.Variable(
                        enabled=variable['enabled'],
                        key=variable['key'],
                        value=variable['value'],
                    )
                )

            create_environment_resp = self.environments_repo.create(
                environment=Environment(
                    name=environment['name'], variables=variables
                )
            )
            if not create_environment_resp.ok:
                raise _ImportFailedError()
        except _ImportInvalidFileError:
            QMessageBox.critical(
                self,
                'Error',
                'Invalid environment file',
            )
            return
        except _ImportFailedError:
            QMessageBox.critical(
                self,
                'Error',
                'Failed to import environment',
            )
            return
        except Exception:
            QMessageBox.critical(
                self,
                'Error',
                'Failed to import environment; unexpected error: {error}',
            )
            return

        self.environments_screen._populate_environments()
        QMessageBox.information(
            self, 'Information', 'Postman environment imported'
        )

    def _on_import_postman_collection(self) -> None:
        try:
            file, _ = QFileDialog.getOpenFileName(
                self,
                'Import Postman Collection',
                '',
                'JSON files (*.json)',
            )

            if not file:
                return

            file = Path(file)

            try:
                collection = json.loads(file.read_text())
            except Exception as error:
                raise _ImportInvalidFileError() from error

            if 'v2.1' not in collection['info']['schema']:
                raise _ImportInvalidVersionError()

            with self.db_manager.session_scope() as session:
                create_folder_resp = self.folders_repo.create(
                    folder=Folder(
                        parent_id=None, name=collection['info']['name']
                    ),
                    session=session,
                )
                if not create_folder_resp.ok:
                    raise _ImportFailedError()
                root_folder = create_folder_resp.data

                postman_items_stack = [
                    (item, root_folder.id)
                    for item in collection.get('item', [])
                ]
                while postman_items_stack:
                    postman_item, parent_folder_id = postman_items_stack.pop()

                    is_request = 'request' in postman_item
                    is_folder = 'item' in postman_item

                    if is_request:
                        request_block = postman_item.get('request', {})
                        url_block = request_block.get('url', {})
                        body_block = request_block.get('body', {})
                        auth_block = request_block.get('auth', {})

                        headers = [
                            Request.Header(
                                enabled=not header.get('disabled', False),
                                key=header['key'] or '',
                                value=header['value'] or '',
                            )
                            for header in request_block.get('header', [])
                        ]
                        params = [
                            Request.Param(
                                enabled=not param.get('disabled', False),
                                key=param['key'] or '',
                                value=param['value'] or '',
                            )
                            for param in url_block.get('query', [])
                        ]

                        body_enabled = False
                        body_mode = BodyMode.RAW
                        body = Request.RawBody(
                            language=BodyRawLanguage.PLAIN, value=''
                        )
                        if body_block:
                            if body_block['mode'] == 'raw':
                                postman_language_to_restiny_language = {
                                    'json': BodyRawLanguage.JSON,
                                    'html': BodyRawLanguage.HTML,
                                    'xml': BodyRawLanguage.XML,
                                }
                                body_enabled = True
                                body_mode = BodyMode.RAW
                                body = Request.RawBody(
                                    language=postman_language_to_restiny_language.get(
                                        body_block.get('options', {})
                                        .get('raw', {})
                                        .get('language'),
                                        BodyRawLanguage.PLAIN,
                                    ),
                                    value=request_block['body']['raw'],
                                )
                            elif body_block['mode'] == 'formdata':
                                body_enabled = True
                                body_mode = BodyMode.FORM_MULTIPART
                                body = Request.MultipartFormBody(
                                    fields=[
                                        Request.MultipartFormBody.Field(
                                            value_kind=field['type'],
                                            enabled=not field.get(
                                                'disabled', False
                                            ),
                                            key=field['key'],
                                            value=field['value']
                                            if field['type'] == 'text'
                                            else None,
                                        )
                                        for field in body_block['formdata']
                                    ]
                                )
                            elif body_block['mode'] == 'urlencoded':
                                body_enabled = True
                                body_mode = BodyMode.FORM_URLENCODED
                                body = Request.UrlEncodedFormBody(
                                    fields=[
                                        Request.UrlEncodedFormBody.Field(
                                            enabled=not field.get(
                                                'disabled', False
                                            ),
                                            key=field['key'],
                                            value=field['value'],
                                        )
                                        for field in body_block['urlencoded']
                                    ]
                                )

                        auth_enabled = False
                        auth_mode = AuthMode.BASIC
                        auth = Request.BasicAuth(username='', password='')
                        if auth_block:
                            if auth_block['type'] == 'basic':
                                auth_enabled = True
                                auth_mode = AuthMode.BASIC
                                auth_basic_username = ''
                                auth_basic_password = ''
                                for item in auth_block['basic']:
                                    if item['key'] == 'username':
                                        auth_basic_username = item['value']
                                    elif item['key'] == 'password':
                                        auth_basic_password = item['value']
                                auth = Request.BasicAuth(
                                    username=auth_basic_username,
                                    password=auth_basic_password,
                                )
                            elif auth_block['type'] == 'bearer':
                                auth_enabled = True
                                auth_mode = AuthMode.BEARER
                                auth = Request.BearerAuth(
                                    token=auth_block['bearer'][0]['value']
                                )
                            elif auth_block['type'] == 'apikey':
                                auth_enabled = True
                                auth_mode = AuthMode.API_KEY
                                auth_api_key_key = ''
                                auth_api_key_value = ''
                                auth_api_key_where = ''
                                for item in auth_block['apikey']:
                                    if item['key'] == 'key':
                                        auth_api_key_key = item['value']
                                    elif item['key'] == 'value':
                                        auth_api_key_value = item['value']
                                    elif item['key'] == 'in':
                                        auth_api_key_where = item['value']
                                auth = Request.ApiKeyAuth(
                                    key=auth_api_key_key,
                                    value=auth_api_key_value,
                                    where=auth_api_key_where,
                                )
                            elif auth_block['type'] == 'digest':
                                auth_enabled = True
                                auth_mode = AuthMode.DIGEST
                                auth_digest_username = ''
                                auth_digest_password = ''
                                for item in auth_block['digest']:
                                    if item['key'] == 'username':
                                        auth_digest_username = item['value']
                                    elif item['key'] == 'password':
                                        auth_digest_password = item['value']
                                auth = Request.DigestAuth(
                                    username=auth_digest_username,
                                    password=auth_digest_password,
                                )

                        create_request_resp = self.requests_repo.create(
                            request=Request(
                                folder_id=parent_folder_id,
                                name=postman_item['name'],
                                method=request_block['method'],
                                url=url_block['raw'],
                                headers=headers,
                                params=params,
                                body_enabled=body_enabled,
                                body_mode=body_mode,
                                body=body,
                                auth_enabled=auth_enabled,
                                auth_mode=auth_mode,
                                auth=auth,
                            ),
                            session=session,
                        )
                        if not create_request_resp.ok:
                            raise _ImportFailedError()
                    elif is_folder:
                        create_folder_resp = self.folders_repo.create(
                            folder=Folder(
                                parent_id=parent_folder_id,
                                name=postman_item['name'],
                            ),
                            session=session,
                        )
                        if not create_folder_resp.ok:
                            raise _ImportFailedError()
                        folder = create_folder_resp.data

                        for subitem in postman_item.get('item', []):
                            postman_items_stack.append((subitem, folder.id))
        except _ImportInvalidFileError:
            QMessageBox.critical(
                self,
                'Error',
                'Invalid collection file',
            )
            return
        except _ImportInvalidVersionError:
            QMessageBox.critical(
                self,
                'Error',
                'Invalid collection version (only v2.1 is supported)',
            )
            return
        except _ImportFailedError:
            QMessageBox.critical(
                self, 'Error', 'Failed to import the collection'
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to import the collection; unexpected error: {error}',
            )
            return

        self.collections_screen._populate_collections_tree()
        QMessageBox.information(
            self,
            'Information',
            'PPostman collection imported',
        )

    def _on_import_environment(self) -> None:
        file, _ = QFileDialog.getOpenFileName(
            self,
            'Import environment',
            '',
            'JSON files (*.json)',
        )
        if not file:
            return

        file = Path(file)
        try:
            data = json.loads(file.read_text())
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.critical(
                self,
                'Import environment',
                f'Error reading file:\n{error}',
            )
            return

        try:
            exported_environment_file = (
                ExportedEnvironmentFileV1.model_validate(data)
            )
        except ValidationError as error:
            QMessageBox.critical(
                self,
                'Import environment',
                f'Error validating the environment:\n{error}',
            )
            return

        self.environments_repo.create(
            exported_environment_file.environment.to_domain()
        )

        self.environments_screen._populate_environments()
        QMessageBox.information(
            self,
            'Information',
            'Environment imported',
        )

    def _on_export_environment(self) -> None:
        environments = self.environments_repo.get_all().data
        environments = [env for env in environments if env.name != 'global']

        if not environments:
            QMessageBox.warning(
                self, 'Export environment', 'No environments available'
            )
            return

        envs_by_name = {env.name: env for env in environments}
        env_name, confirmed = QInputDialog.getItem(
            self,
            'Export environment',
            'Select an environment:',
            list(envs_by_name),
            editable=False,
        )
        if not confirmed:
            return

        environment = envs_by_name[env_name]

        file, _ = QFileDialog.getSaveFileName(
            self,
            'Export environment',
            f'{environment.name}.json',
            'JSON files (*.json)',
        )
        if not file:
            return

        file = Path(file)
        if file.suffix != '.json':
            file = file.with_suffix('.json')

        data = {
            'format': 'restiny-environment',
            'version': 1,
            'environment': environment.model_dump(
                exclude=['id', 'created_at', 'updated_at']
            ),
        }

        try:
            file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str)
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                'Export environment',
                f'Could not export environment:\n{error}',
            )
            return

        QMessageBox.information(
            self,
            'Information',
            'Environment exported',
        )

    def _on_import_collection(self) -> None:
        file, _ = QFileDialog.getOpenFileName(
            self, 'Import Collection', '', 'JSON files (*.json)'
        )
        if not file:
            return

        file = Path(file)
        try:
            data = json.loads(file.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.critical(
                self,
                'Import Collection',
                f'Could not read collection:\n{error}',
            )
            return

        try:
            exported_collection_file = ExportedCollectionFileV1.model_validate(
                data
            )
        except ValidationError as error:
            QMessageBox.critical(
                self,
                'Import Collection',
                f'Error validating the collection:\n{error}',
            )
            return

        collection = exported_collection_file.collection
        id_map: dict[str, int] = {}

        root_folder = self.folders_repo.create(
            Folder(parent_id=None, name=collection.name, uuid=collection.uuid)
        ).data
        id_map[str(root_folder.uuid)] = root_folder.id

        for folder in collection.folders:
            parent_id = (
                id_map.get(str(folder.parent_uuid))
                if folder.parent_uuid
                else None
            )
            new_folder = self.folders_repo.create(
                folder.to_domain(parent_id)
            ).data
            id_map[str(folder.uuid)] = new_folder.id

        for req in collection.requests:
            folder_id = id_map[str(req.folder_uuid)]
            new_request = req.to_domain(folder_id)
            self.requests_repo.create(new_request)

        self.collections_screen._populate_collections_tree()
        QMessageBox.information(self, 'Information', 'Collection imported')

    def _on_export_collection(self) -> None:
        collections = self.folders_repo.get_roots().data
        if not collections:
            QMessageBox.warning(
                self, 'Export Collection', 'No collections available'
            )
            return

        collections_by_name = {c.name: c for c in collections}
        collection_name, confirmed = QInputDialog.getItem(
            self,
            'Export Collection',
            'Select a collection:',
            list(collections_by_name),
            editable=False,
        )
        if not confirmed:
            return

        collection = collections_by_name[collection_name]

        file, _ = QFileDialog.getSaveFileName(
            self,
            'Export Collection',
            f'{collection.name}.json',
            'JSON files (*.json)',
        )
        if not file:
            return

        file = Path(file)
        if file.suffix != '.json':
            file = file.with_suffix('.json')

        all_folders, all_requests = [], []

        def collect(folder):
            for child in self.folders_repo.get_by_parent_id(folder.id).data:
                obj = {'parent_uuid': str(folder.uuid)}
                obj.update(
                    child.model_dump(
                        exclude=['id', 'created_at', 'updated_at', 'parent_id']
                    )
                )
                all_folders.append(obj)
                collect(child)
            for req in self.requests_repo.get_by_folder_id(folder.id).data:
                obj = {'folder_uuid': str(folder.uuid)}
                obj.update(
                    req.model_dump(
                        exclude=['id', 'created_at', 'updated_at', 'folder_id']
                    )
                )
                all_requests.append(obj)

        collect(collection)

        data = {
            'format': 'restiny-collection',
            'version': 1,
            'collection': {
                'uuid': str(collection.uuid),
                'name': collection.name,
                'folders': all_folders,
                'requests': all_requests,
            },
        }

        for req in data['collection']['requests']:
            if req['body']['language'] == BodyRawLanguage.JSON:
                req['body']['value'] = json.loads(req['body']['value'])

        try:
            file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str)
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                'Export Collection',
                f'Could not export collection:\n{error}',
            )
            return

        QMessageBox.information(self, 'Information', 'Collection exported')

    def _on_export_request_as_curl(self) -> None:
        if not self.collections_screen._selected_request:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText('No selected request')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        QApplication.clipboard().setText(
            self.collections_screen.get_resolved_request().to_curl()
        )
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText('cURL command copied to clipboard')
        msg.setWindowTitle('Information')
        msg.exec()

    def _load_openapi_spec(self, spec_file: Path) -> tuple[dict, str]:
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

    def _import_openapi_spec_v2_0(self) -> None:
        with self.db_manager.session_scope() as session:
            create_resp = self.folders_repo.create(
                session=session,
                folder=Folder(parent_id=None, name=self.spec['info']['title']),
            )
            if not create_resp.ok:
                raise _ImportFailedError()
            root_folder = create_resp.data

            tag_name_to_folder: dict[str, Folder] = {}
            for tag in self.spec['tags']:
                create_resp = self.folders_repo.create(
                    session=session,
                    folder=Folder(parent_id=root_folder.id, name=tag['name']),
                )
                if not create_resp.ok:
                    raise _ImportFailedError()
                folder = create_resp.data
                tag_name_to_folder[tag['name']] = folder

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
                    body = Request.RawBody(
                        language=BodyRawLanguage.PLAIN, value=''
                    )

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
                    name = (
                        operation.get('operationId')
                        or operation.get('summary')
                        or path.lstrip('/')
                    )
                    existing = self.requests_repo.get_by_name_and_folder_id(
                        name, folder_id
                    )
                    if existing:
                        name = f'{name}_{uuid4().hex[:6]}'
                    create_req_resp = self.requests_repo.create(
                        session=session,
                        request=Request(
                            folder_id=folder_id,
                            name=name,
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

    def _import_openapi_spec_v3_0(self) -> None:
        with self.db_manager.session_scope() as session:
            create_resp = self.folders_repo.create(
                session=session,
                folder=Folder(parent_id=None, name=self.spec['info']['title']),
            )
            if not create_resp.ok:
                raise _ImportFailedError()
            root_folder = create_resp.data

            tag_name_to_folder: dict[str, Folder] = {}
            for tag in self.spec['tags']:
                create_resp = self.folders_repo.create(
                    session=session,
                    folder=Folder(parent_id=root_folder.id, name=tag['name']),
                )
                if not create_resp.ok:
                    raise _ImportFailedError()
                folder = create_resp.data
                tag_name_to_folder[tag['name']] = folder

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
                    body = Request.RawBody(
                        language=BodyRawLanguage.PLAIN, value=''
                    )

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
                    create_req_resp = self.requests_repo.create(
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

        # openapi 2.0
        if ref.startswith('#/definitions/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['definitions'][schema_name]
        if ref.startswith('#/parameters/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['parameters'][schema_name]
        if ref.startswith('#/responses/'):
            schema_name = ref.rsplit('/', 1)[-1]
            return self.spec['responses'][schema_name]

        # openapi 3.0
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
