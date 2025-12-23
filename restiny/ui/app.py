import asyncio
import json
from collections.abc import Iterable
from http import HTTPStatus

import httpx
import pyperclip
from textual import on
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import DescendantFocus
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header

from restiny.__about__ import __version__
from restiny.assets import STYLE_TCSS
from restiny.consts import CUSTOM_THEMES
from restiny.data.db import DBManager
from restiny.data.repos import (
    AuthPresetsSQLRepo,
    EnvironmentsSQLRepo,
    FoldersSQLRepo,
    RequestsSQLRepo,
    SettingsSQLRepo,
)
from restiny.entities import AuthPreset, Environment, Request
from restiny.enums import (
    BodyMode,
    BodyRawLanguage,
    ContentType,
)
from restiny.ui import (
    CollectionsArea,
    RequestArea,
    ResponseArea,
    TopBarArea,
    URLArea,
)
from restiny.ui.screens.auth_presets_screen import AuthPresetsScreen
from restiny.ui.screens.environments_screen import EnvironmentsScreen
from restiny.ui.screens.openapi_spec_import_screen import (
    OpenapiSpecImportScreen,
)
from restiny.ui.screens.postman_collection_import_screen import (
    PostmanCollectionImportScreen,
)
from restiny.ui.screens.postman_environment_import_screen import (
    PostmanEnvironmentImportScreen,
)
from restiny.ui.screens.settings_screen import SettingsScreen
from restiny.widgets.custom_text_area import CustomTextArea


class RESTinyApp(App, inherit_bindings=False):
    TITLE = f'RESTiny v{__version__}'
    SUB_TITLE = 'Minimal HTTP client, no bullshit'
    CSS_PATH = STYLE_TCSS
    BINDINGS = [
        Binding(
            key='escape', action='quit', description='Quit the app', show=True
        ),
        Binding(
            key='ctrl+n',
            action='prompt_add',
            description='Add req/folder',
            show=True,
        ),
        Binding(
            key='f2',
            action='prompt_update',
            description='Update req/folder',
            show=True,
        ),
        Binding(
            key='delete',
            action='prompt_delete',
            description='Delete req/folder',
            show=True,
        ),
        Binding(
            key='ctrl+s',
            action='save',
            description='Save req',
            show=True,
        ),
        Binding(
            key='ctrl+b',
            action='toggle_collections',
            description='Toggle collections',
            show=True,
        ),
        Binding(
            key='f10',
            action='maximize_or_minimize_area',
            description='Maximize/Minimize area',
            show=True,
        ),
    ]

    def __init__(
        self,
        db_manager: DBManager,
        folders_repo: FoldersSQLRepo,
        requests_repo: RequestsSQLRepo,
        settings_repo: SettingsSQLRepo,
        environments_repo: EnvironmentsSQLRepo,
        auth_presets_repo: AuthPresetsSQLRepo,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.db_manager = db_manager
        self.folders_repo = folders_repo
        self.requests_repo = requests_repo
        self.settings_repo = settings_repo
        self.environments_repo = environments_repo
        self.auth_presets_repo = auth_presets_repo

        self._active_request_task: asyncio.Task | None = None
        self._last_focused_widget: Widget | None = None
        self._last_focused_maximizable_area: Widget | None = None
        self._selected_request: Request | None = None
        self._request_id_to_response: dict[int, httpx.Response] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield CollectionsArea(classes='w-1fr')
            with Vertical(classes='w-6fr'):
                with Vertical(classes='h-auto'):
                    yield TopBarArea()
                    yield URLArea()
                with Horizontal(classes='h-1fr'):
                    yield RequestArea()
                    yield ResponseArea()
        yield Footer()

    def on_mount(self) -> None:
        self.collections_area = self.query_one(CollectionsArea)
        self.top_bar_area = self.query_one(TopBarArea)
        self.url_area = self.query_one(URLArea)
        self.request_area = self.query_one(RequestArea)
        self.response_area = self.query_one(ResponseArea)

        self.selected_request = None

        self._register_themes()
        self._apply_settings()

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield SystemCommand('Copy as cURL', None, self.copy_as_curl)
        yield SystemCommand(
            'Show/Hide keys and help panel',
            None,
            self.toggle_help_panel,
        )
        yield SystemCommand(
            'Save screenshot',
            None,
            lambda: self.set_timer(0.1, self.deliver_screenshot),
        )
        yield SystemCommand(
            'Manage environments', None, self.manage_environments
        )
        yield SystemCommand('Manage settings', None, self.manage_settings)
        yield SystemCommand(
            'Manage auth presets', None, self.manage_auth_presets
        )
        yield SystemCommand(
            'Import postman collection',
            None,
            self.import_postman_collection,
        )
        yield SystemCommand(
            'Import postman environment', None, self.import_postman_environment
        )
        yield SystemCommand(
            'Import openapi spec', None, self.import_openapi_spec
        )

    def action_toggle_collections(self) -> None:
        if self.collections_area.display:
            self.collections_area.display = False
        else:
            self.collections_area.display = True

    def action_prompt_add(self) -> None:
        self.collections_area.prompt_add()

    def action_prompt_update(self) -> None:
        self.collections_area.prompt_update()

    def action_prompt_delete(self) -> None:
        self.collections_area.prompt_delete()

    def action_save(self) -> None:
        if not self.selected_request:
            self.notify('No request selected', severity='warning')
            return

        req = self.get_request()
        self.requests_repo.update(request=req)
        self.collections_area.populate_children(
            self.collections_area.collections_tree.current_parent_folder
        )
        self.notify('Saved changes', severity='information')

    def action_maximize_or_minimize_area(self) -> None:
        if not self._last_focused_maximizable_area:
            self.notify('No area focused', severity='warning')
            return

        if self.screen.maximized:
            self.screen.minimize()
        else:
            self.screen.maximize(self._last_focused_maximizable_area)

    def toggle_help_panel(self) -> None:
        if self.query('HelpPanel'):
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()

    def copy_as_curl(self) -> None:
        if not self.selected_request:
            self.notify(
                'No request selected',
                severity='warning',
            )
            return

        request, auth = self.get_resolved_request_with_auth()
        self.copy_to_clipboard(request.to_curl(auth=auth))
        self.notify(
            'CURL command copied to clipboard',
            severity='information',
        )

    def manage_settings(self) -> None:
        def on_settings_result(result: bool) -> None:
            if result is False:
                return

            self._apply_settings()

        self.push_screen(
            screen=SettingsScreen(),
            callback=on_settings_result,
        )

    def manage_environments(self) -> None:
        def on_manage_environments_result(result) -> None:
            self.top_bar_area.populate()

        self.push_screen(
            screen=EnvironmentsScreen(), callback=on_manage_environments_result
        )

    def manage_auth_presets(self) -> None:
        def on_manage_auth_presets_result(result) -> None:
            pass

        self.push_screen(
            screen=AuthPresetsScreen(), callback=on_manage_auth_presets_result
        )

    def import_postman_collection(self) -> None:
        def on_import_postman_collection_result(result: bool) -> None:
            if result is False:
                return

            self.collections_area.populate_children(
                self.collections_area.collections_tree.root
            )

        self.push_screen(
            screen=PostmanCollectionImportScreen(),
            callback=on_import_postman_collection_result,
        )

    def import_postman_environment(self) -> None:
        def on_import_postman_environment_result(result: bool) -> None:
            if result is False:
                return

            self.top_bar_area.populate()

        self.push_screen(
            screen=PostmanEnvironmentImportScreen(),
            callback=on_import_postman_environment_result,
        )

    def import_openapi_spec(self) -> None:
        def on_import_openapi_spec(result: bool) -> None:
            if result is False:
                return

            self.collections_area.populate_children(
                self.collections_area.collections_tree.root
            )

        self.push_screen(
            screen=OpenapiSpecImportScreen(), callback=on_import_openapi_spec
        )

    def copy_to_clipboard(self, text: str) -> None:
        super().copy_to_clipboard(text)
        try:
            # Also copy to the system clipboard (outside of the app)
            pyperclip.copy(text)
        except Exception:
            pass

    def bell(self) -> None:
        """
        Override Textual's bell method to suppress terminal beep sounds
        """
        pass

    @on(DescendantFocus)
    def _on_focus(self, event: DescendantFocus) -> None:
        self._last_focused_widget = event.widget
        _last_focused_maximizable_area = self._find_maximizable_area_by_widget(
            widget=event.widget
        )
        if _last_focused_maximizable_area:
            self._last_focused_maximizable_area = (
                _last_focused_maximizable_area
            )

    @on(URLArea.SendRequest)
    def _on_send_request(self, message: URLArea.SendRequest) -> None:
        self._active_request_task = asyncio.create_task(self._send_request())

    @on(URLArea.CancelRequest)
    def _on_cancel_request(self, message: URLArea.CancelRequest) -> None:
        if self._active_request_task and not self._active_request_task.done():
            self._active_request_task.cancel()

    @on(CollectionsArea.RequestSelected)
    def _on_request_selected(
        self, message: CollectionsArea.RequestSelected
    ) -> None:
        request = self.requests_repo.get_by_id(id=message.request_id).data
        self.selected_request = request
        self.set_request(request=request)

        if request.id in self._request_id_to_response.keys():
            self._display_response(self._request_id_to_response[request.id])
            self.response_area.is_showing_response = True
        else:
            self.response_area.clear()
            self.response_area.is_showing_response = False

    @on(CollectionsArea.RequestUpdated)
    def _on_request_updated(self, message) -> None:
        req = self.requests_repo.get_by_id(id=message.request_id).data
        self.selected_request = req

    @on(CollectionsArea.RequestDeleted)
    def _on_request_deleted(self, message) -> None:
        self.selected_request = None

    @on(CollectionsArea.FolderSelected)
    def _on_folder_selected(self, message) -> None:
        self.selected_request = None

    def _apply_settings(self) -> None:
        settings = self.settings_repo.get().data
        self.theme = settings.theme
        for text_area in self.query(CustomTextArea):
            text_area.theme = settings.theme

    def _register_themes(self) -> None:
        for theme in CUSTOM_THEMES.values():
            self.register_theme(theme=theme['global'])

        for text_area in self.query(CustomTextArea):
            for theme in CUSTOM_THEMES.values():
                text_area.register_theme(theme=theme['text_area'])

    def _find_maximizable_area_by_widget(
        self, widget: Widget
    ) -> Widget | None:
        while widget is not None:
            if (
                isinstance(widget, CollectionsArea)
                or isinstance(widget, URLArea)
                or isinstance(widget, RequestArea)
                or isinstance(widget, ResponseArea)
            ):
                return widget
            widget = widget.parent

    @property
    def selected_request(self) -> Request | None:
        return self._selected_request

    @selected_request.setter
    def selected_request(self, request: Request | None) -> None:
        if request is None:
            self.url_area.clear()
            self.request_area.clear()
            self.response_area.clear()
            self.url_area.disabled = True
            self.request_area.disabled = True
            self.response_area.disabled = True
            self.response_area.is_showing_response = False
        else:
            self.url_area.disabled = False
            self.request_area.disabled = False
            self.response_area.disabled = False

        self._selected_request = request

    def get_request(self) -> Request:
        method = self.url_area.method
        url = self.url_area.url

        headers = [
            Request.Header(
                enabled=header['enabled'],
                key=header['key'],
                value=header['value'],
            )
            for header in self.request_area.headers
        ]

        params = [
            Request.Param(
                enabled=param['enabled'],
                key=param['key'],
                value=param['value'],
            )
            for param in self.request_area.params
        ]

        auth_enabled = self.request_area.auth_enabled
        auth_id = self.request_area.auth_id

        body_enabled = self.request_area.body_enabled
        body_mode = self.request_area.body_mode
        body = None
        if body_mode == BodyMode.RAW:
            body = Request.RawBody(
                language=BodyRawLanguage(self.request_area.body_raw_language),
                value=self.request_area.body_raw,
            )
        elif body_mode == BodyMode.FILE:
            body = Request.FileBody(file=self.request_area.body_file)
        elif body_mode == BodyMode.FORM_URLENCODED:
            body = Request.UrlEncodedFormBody(
                fields=[
                    Request.UrlEncodedFormBody.Field(
                        enabled=form_field['enabled'],
                        key=form_field['key'],
                        value=form_field['value'],
                    )
                    for form_field in self.request_area.body_form_urlencoded
                ]
            )
        elif body_mode == BodyMode.FORM_MULTIPART:
            body = Request.MultipartFormBody(
                fields=[
                    Request.MultipartFormBody.Field(
                        enabled=form_field['enabled'],
                        key=form_field['key'],
                        value=form_field['value'],
                        value_kind=form_field['value_kind'],
                    )
                    for form_field in self.request_area.body_form_multipart
                ]
            )

        options = Request.Options(
            timeout=self.request_area.option_timeout,
            follow_redirects=self.request_area.option_follow_redirects,
            verify_ssl=self.request_area.option_verify_ssl,
        )

        return Request(
            id=self.selected_request.id,
            folder_id=self.selected_request.folder_id,
            name=self.selected_request.name,
            method=method,
            url=url,
            headers=headers,
            params=params,
            body_enabled=body_enabled,
            body_mode=body_mode,
            body=body,
            auth_enabled=auth_enabled,
            auth_id=auth_id,
            options=options,
        )

    def get_variables(self) -> list[Environment.Variable]:
        variables: list[Environment.Variable] = []

        global_environment = self.environments_repo.get_by_name(
            name='global'
        ).data
        variables.extend(global_environment.resolve_variables().variables)

        if self.top_bar_area.environment:
            environment = self.environments_repo.get_by_name(
                name=self.top_bar_area.environment
            ).data
            variables.extend(environment.resolve_variables().variables)

        return variables

    def get_resolved_request_with_auth(
        self,
    ) -> tuple[Request, AuthPreset | None]:
        variables = self.get_variables()
        request = self.get_request().resolve_variables(variables=variables)

        auth_preset: AuthPreset | None = None
        if request.auth_enabled and request.auth_id:
            auth_preset = self.auth_presets_repo.get_by_id(
                id=request.auth_id
            ).data
            auth_preset = auth_preset.resolve_variables(variables=variables)

        return request, auth_preset

    def set_request(self, request: Request) -> None:
        self.url_area.clear()
        self.request_area.clear()

        self.url_area.method = request.method
        self.url_area.url = request.url

        self.request_area.headers = [
            {
                'enabled': header.enabled,
                'key': header.key,
                'value': header.value,
            }
            for header in request.headers
        ]
        self.request_area.params = [
            {'enabled': param.enabled, 'key': param.key, 'value': param.value}
            for param in request.params
        ]

        self.request_area.auth_enabled = request.auth_enabled
        self.request_area.auth_id = request.auth_id

        self.request_area.body_enabled = request.body_enabled
        self.request_area.body_mode = request.body_mode
        if request.body is not None:
            if request.body_mode == BodyMode.RAW:
                self.request_area.body_raw_language = request.body.language
                self.request_area.body_raw = request.body.value
            elif request.body_mode == BodyMode.FILE:
                self.request_area.body_file = request.body.file
            elif request.body_mode == BodyMode.FORM_URLENCODED:
                self.request_area.body_form_urlencoded = [
                    {
                        'enabled': form_field.enabled,
                        'key': form_field.key,
                        'value': form_field.value,
                    }
                    for form_field in request.body.fields
                ]
            elif request.body_mode == BodyMode.FORM_MULTIPART:
                self.request_area.body_form_multipart = [
                    {
                        'enabled': form_field.enabled,
                        'key': form_field.key,
                        'value': form_field.value,
                        'value_kind': form_field.value_kind,
                    }
                    for form_field in request.body.fields
                ]

        self.request_area.option_follow_redirects = (
            request.options.follow_redirects
        )
        self.request_area.option_verify_ssl = request.options.verify_ssl
        self.request_area.option_timeout = str(request.options.timeout)

    async def _send_request(self) -> None:
        self.response_area.clear()
        self.response_area.loading = True
        self.url_area.request_pending = True
        try:
            request, auth = self.get_resolved_request_with_auth()
            async with httpx.AsyncClient(
                timeout=request.options.timeout,
                follow_redirects=request.options.follow_redirects,
                verify=request.options.verify_ssl,
            ) as http_client:
                response = await http_client.send(
                    request=request.to_httpx_req(),
                    auth=auth.to_httpx_auth() if auth else None,
                )
                self._display_response(response=response)
                self.response_area.is_showing_response = True

                self._request_id_to_response[request.id] = response
        except httpx.RequestError as error:
            error_name = type(error).__name__
            error_message = str(error)
            if error_message:
                self.notify(f'{error_name}: {error_message}', severity='error')
            else:
                self.notify(f'{error_name}', severity='error')
            self.response_area.clear()
            self.response_area.is_showing_response = False
        except asyncio.CancelledError:
            self.response_area.clear()
            self.response_area.is_showing_response = False
        finally:
            self.response_area.loading = False
            self.url_area.request_pending = False

    def _display_response(self, response: httpx.Response) -> None:
        content_type_to_body_language = {
            ContentType.TEXT: BodyRawLanguage.PLAIN,
            ContentType.HTML: BodyRawLanguage.HTML,
            ContentType.JSON: BodyRawLanguage.JSON,
            ContentType.YAML: BodyRawLanguage.YAML,
            ContentType.XML: BodyRawLanguage.XML,
        }

        self.response_area.status = HTTPStatus(response.status_code)
        self.response_area.content_size = response.num_bytes_downloaded
        self.response_area.elapsed_time = round(
            response.elapsed.total_seconds(), 2
        )
        self.response_area.headers = {
            header_key: header_value
            for header_key, header_value in response.headers.multi_items()
        }
        self.response_area.body_raw_language = (
            content_type_to_body_language.get(
                response.headers.get('Content-Type'), BodyRawLanguage.PLAIN
            )
        )
        if self.response_area.body_raw_language == BodyRawLanguage.JSON:
            indented_body_raw = json.dumps(json.loads(response.text), indent=4)
            self.response_area.body_raw = indented_body_raw
        else:
            self.response_area.body_raw = response.text
