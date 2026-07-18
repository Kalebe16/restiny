import asyncio
import json
import mimetypes
from http import HTTPStatus
from pathlib import Path

import httpx
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from restiny.data.repos import (
    EnvironmentsSQLRepo,
    FoldersSQLRepo,
    RequestsSQLRepo,
)
from restiny.entities import Folder, Request
from restiny.enums import (
    AuthMode,
    BodyMode,
    BodyRawLanguage,
    ContentType,
    HTTPMethod,
)
from restiny.ui.request_area import RequestArea
from restiny.ui.response_area import ResponseArea
from restiny.ui.top_bar_area import TopBarArea
from restiny.ui.url_area import URLArea
from restiny.widgets.collections_tree import CollectionsTree


def _is_textual_mimetype(mimetype: str) -> bool:
    mimetype = mimetype.lower()

    if mimetype.startswith('text'):
        return True

    if mimetype.endswith('json'):
        return True

    if mimetype.endswith('xml'):
        return True

    if mimetype.endswith('yaml'):
        return True

    if mimetype.endswith('javascript'):
        return True

    return False


class CollectionsScreen(QWidget):
    def __init__(
        self,
        main_window: QMainWindow,
        folders_repo: FoldersSQLRepo,
        requests_repo: RequestsSQLRepo,
        environments_repo: EnvironmentsSQLRepo,
    ):
        super().__init__()
        self.main_window = main_window
        self.folders_repo = folders_repo
        self.requests_repo = requests_repo
        self.environments_repo = environments_repo
        self._active_request_task: asyncio.Task | None = None
        self._collections_tree_showing = True
        self._cookies: httpx.Cookies = httpx.Cookies()
        self._opened_requests: dict[int, Request] = {}
        self._selected_request: Request | None = None
        self._request_id_to_response: dict[int, httpx.Response] = {}

        self.collections_tree = CollectionsTree()
        self.collections_tree.setHeaderHidden(True)
        self.collections_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.collections_tree.setColumnCount(2)
        self.collections_tree.setHeaderLabels(['Method', 'Name'])
        header = self.collections_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # método
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self._populate_collections_tree(None)

        def open_menu(pos):
            item = self.collections_tree.itemAt(pos)
            menu = QMenu(self.collections_tree)

            if item:
                item_type = item.data(0, Qt.UserRole)['type']

                if item_type == 'folder':
                    menu.addAction(
                        'Add folder',
                        lambda: self._on_add_folder(as_root=False),
                    )
                    menu.addAction(
                        'Add request',
                        lambda: self._on_add_request(as_root=False),
                    )
                    menu.addAction('Move', self._on_move_folder)
                    menu.addAction('Rename', self._on_rename_folder)
                    menu.addAction('Remove', self._on_remove_folder)
                elif item_type == 'request':
                    menu.addAction('Move', self._on_move_request)
                    menu.addAction('Rename', self._on_rename_request)
                    menu.addAction('Remove', self._on_remove_request)
            else:
                menu.addAction(
                    'Add folder', lambda: self._on_add_folder(as_root=True)
                )
                menu.addAction(
                    'Add request', lambda: self._on_add_request(as_root=True)
                )

            menu.exec(self.collections_tree.viewport().mapToGlobal(pos))

        self.collections_tree.customContextMenuRequested.connect(open_menu)

        self.top_bar_area = TopBarArea(
            environments_repo=self.environments_repo,
            requests_repo=self.requests_repo,
        )
        self.url_area = URLArea()
        self.request_area = RequestArea()
        self.response_area = ResponseArea()

        first_row = QHBoxLayout()
        first_row.addWidget(self.top_bar_area)

        second_row = QHBoxLayout()
        second_row.addWidget(self.url_area)

        third_row = QHBoxLayout()
        third_row.addWidget(self.request_area, 1)
        third_row.addWidget(self.response_area, 1)

        main_content = QVBoxLayout()
        main_content.addLayout(first_row)
        main_content.addLayout(second_row)
        main_content.addLayout(third_row)

        layout = QHBoxLayout(self)
        layout.addWidget(self.collections_tree, 1)
        layout.addLayout(main_content, 8)

        self.request_area.sig_edited.connect(self._on_request_edited)
        self.url_area.sig_edited.connect(self._on_request_edited)
        self.url_area.sig_send_requested.connect(
            self._on_send_request_requested
        )
        self.url_area.sig_download_requested.connect(
            self._on_download_request_requested
        )
        self.url_area.sig_cancel_requested.connect(
            self._on_cancel_request_requested
        )
        self.collections_tree.itemSelectionChanged.connect(
            self._on_request_or_folder_selected
        )
        self.top_bar_area.sig_tab_selected.connect(self._on_tab_selected)
        self.top_bar_area.sig_all_tabs_closed.connect(self._on_all_tabs_closed)
        self.top_bar_area.sig_tab_closed.connect(self._on_tab_closed)

        toggle_sidebar_shortcut = QShortcut(QKeySequence('Ctrl+B'), self)
        toggle_sidebar_shortcut.activated.connect(
            self._on_toggle_collections_tree
        )
        save_request_shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        save_request_shortcut.activated.connect(self._on_request_saved)

        self.url_area.clear_data()
        self.request_area.clear_data()
        self.url_area.setDisabled(True)
        self.request_area.setDisabled(True)

    def _on_move_folder(self) -> None:
        folder_id = self.collections_tree.currentItemData()['id']
        parent_id = self.folders_repo.get_by_id(folder_id).data.parent_id

        dialog = MoveFolderDialog(
            parent=self,
            folders_repo=self.folders_repo,
            folder_id=folder_id,
            parent_id=parent_id,
        )
        dialog.sig_folder_moved.connect(
            lambda folder: self.collections_tree.move_folder(
                folder, folder.parent_id
            )
        )
        dialog.exec()

    def _on_move_request(self) -> None:
        request_id = self.collections_tree.currentItemData()['id']
        folder_id = self.requests_repo.get_by_id(id=request_id).data.folder_id

        dialog = MoveRequestDialog(
            parent=self,
            requests_repo=self.requests_repo,
            folders_repo=self.folders_repo,
            request_id=request_id,
            folder_id=folder_id,
        )
        dialog.sig_request_moved.connect(
            lambda request: self.collections_tree.move_request(
                request, request.folder_id
            )
        )
        dialog.exec()

    def _on_all_tabs_closed(self) -> None:
        self._selected_request = None
        self._opened_requests = {}
        self.collections_tree.clearSelection()
        self.collections_tree.setCurrentItem(None)
        self.url_area.clear_data()
        self.request_area.clear_data()
        self.url_area.setDisabled(True)
        self.request_area.setDisabled(True)

    def _on_request_edited(self) -> None:
        if not self._selected_request:
            return

        current_request = self.get_request()
        saved_request = self.requests_repo.get_by_id(current_request.id).data

        if not saved_request:
            return

        current_hash = current_request.gen_hash()
        saved_hash = saved_request.gen_hash()

        if current_hash != saved_hash:
            self.top_bar_area.mark_unsaved_tab(current_request.id)
        else:
            self.top_bar_area.mark_saved_tab(current_request.id)

        self._opened_requests[current_request.id] = current_request

    def _on_tab_selected(self, request_id: int) -> None:
        request = self._opened_requests[request_id]
        self._selected_request = request
        self.set_request(request=request)

        matches = self.collections_tree.findItems(
            '', Qt.MatchContains | Qt.MatchRecursive, 0
        )
        for item in matches:
            data = item.data(0, Qt.UserRole)
            if (
                data
                and data.get('type') == 'request'
                and data.get('id') == request_id
            ):
                self.collections_tree.setCurrentItem(item)
                break

    def _on_tab_closed(self, request_id: int) -> None:
        del self._opened_requests[request_id]

    def _on_request_saved(self) -> None:
        request = self.get_request()
        resp = self.requests_repo.update(request)
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to save request ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        self.top_bar_area.mark_saved_tab(self._selected_request.id)
        self.top_bar_area.update_tabs()
        self.collections_tree.update_request(request)
        self.main_window.statusBar().showMessage('Request saved', 3000)

    def _on_request_or_folder_selected(self) -> None:
        item = self.collections_tree.currentItem()
        if not item:
            return

        if not item.isSelected():
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data.get('type') == 'folder':
            self.top_bar_area.setDisabled(True)
            self.url_area.setDisabled(True)
            self.request_area.setDisabled(True)
            self.response_area.setDisabled(True)
            self._selected_request = None
            self.url_area.clear_data()
            self.request_area.clear_data()
        elif data.get('type') == 'request':
            request_id = data.get('id')
            self.top_bar_area.setDisabled(False)
            self.url_area.setDisabled(False)
            self.request_area.setDisabled(False)
            self.response_area.setDisabled(False)

            if request_id in self._opened_requests:
                request = self._opened_requests[request_id]
            else:
                request = self.requests_repo.get_by_id(id=request_id).data
                self._opened_requests[request.id] = request

            self._selected_request = request
            self.set_request(request)
            self.top_bar_area.open_request_tab(
                request_id=request.id,
                request_name=f'{request.method} {request.name}',
            )
            if request.id in self._request_id_to_response.keys():
                self._display_response(
                    self._request_id_to_response[request.id]
                )
                self.response_area.show_response()
            else:
                self.response_area.clear_data()
                self.response_area.show_empty()

    def _populate_collections_tree(
        self, parent_item: QTreeWidgetItem | None = None
    ) -> None:
        folder_id = None
        if parent_item is not None:
            data = parent_item.data(0, Qt.UserRole)
            if data and data.get('type') == 'folder':
                folder_id = data['id']

        folders = (
            self.folders_repo.get_roots().data
            if folder_id is None
            else self.folders_repo.get_by_parent_id(folder_id).data
        )
        requests = self.requests_repo.get_by_folder_id(folder_id).data

        def sort_requests(request):
            methods = [method.value for method in HTTPMethod]
            method_order = {m: i for i, m in enumerate(methods)}
            return (method_order[request.method], request.name.lower())

        sorted_folders = sorted(folders, key=lambda f: f.name.lower())
        sorted_requests = sorted(requests, key=sort_requests)

        if parent_item is not None:
            parent_item.takeChildren()
        else:
            self.collections_tree.clear()

        for folder in sorted_folders:
            folder_item = self.collections_tree.add_folder(folder, parent_item)
            self._populate_collections_tree(folder_item)

        for request in sorted_requests:
            self.collections_tree.add_request(request, parent_item)

    def _on_toggle_collections_tree(self) -> None:
        if self._collections_tree_showing:
            self.collections_tree.hide()
            self._collections_tree_showing = False
        else:
            self.collections_tree.show()
            self._collections_tree_showing = True

    def _on_send_request_requested(self) -> None:
        self._active_request_task = asyncio.create_task(self._send_request())

    def _on_download_request_requested(self) -> None:
        self._active_request_task = asyncio.create_task(
            self._send_request(download=True)
        )

    def _on_cancel_request_requested(self) -> None:
        if self._active_request_task:
            self._active_request_task.cancel()

    def _on_add_request(self, as_root: bool) -> None:
        item = self.collections_tree.currentItem()
        parent_folder_id = None
        if item:
            parent_folder_id = item.data(0, Qt.UserRole)['id']
        if as_root:
            parent_folder_id = None
            item = None
        dialog = AddRequestDialog(
            parent=self,
            requests_repo=self.requests_repo,
            parent_folder_id=parent_folder_id,
        )
        dialog.sig_request_added.connect(
            lambda request: self.collections_tree.add_request(request, item)
        )
        dialog.exec()

    def _on_add_folder(self, as_root: bool) -> None:
        item = self.collections_tree.currentItem()
        parent_item = None
        parent_folder_id = None
        if item:
            parent_item = item
            parent_folder_id = item.data(0, Qt.UserRole)['id']
        if as_root:
            parent_item = None
            parent_folder_id = None
        dialog = AddFolderDialog(
            parent=self,
            parent_folder_id=parent_folder_id,
            folders_repo=self.folders_repo,
        )
        dialog.sig_folder_added.connect(
            lambda folder: self.collections_tree.add_folder(
                folder, parent_item
            )
        )
        dialog.exec()

    def _on_rename_request(self) -> None:
        request_id = self.collections_tree.currentItemData()['id']
        dialog = RenameRequestDialog(
            parent=self,
            requests_repo=self.requests_repo,
            request_id=request_id,
        )
        dialog.sig_request_renamed.connect(
            lambda request: self.collections_tree.update_request(request)
        )
        dialog.sig_request_renamed.connect(self.top_bar_area.update_tabs)
        dialog.exec()

    def _on_rename_folder(self) -> None:
        folder_id = self.collections_tree.currentItemData()['id']
        dialog = RenameFolderDialog(
            parent=self, folders_repo=self.folders_repo, folder_id=folder_id
        )
        dialog.sig_folder_renamed.connect(
            lambda folder: self.collections_tree.update_folder(folder)
        )
        dialog.exec()

    def _on_remove_request(self) -> None:
        request_id = self.collections_tree.currentItemData()['id']
        dialog = RemoveRequestDialog(
            parent=self,
            requests_repo=self.requests_repo,
            request_id=request_id,
        )
        dialog.sig_request_removed.connect(
            lambda: self.collections_tree.delete_request_by_id(request_id)
        )
        dialog.sig_request_removed.connect(self.top_bar_area.update_tabs)
        dialog.exec()

    def _on_remove_folder(self) -> None:
        folder_id = self.collections_tree.currentItemData()['id']
        dialog = RemoveFolderDialog(
            parent=self,
            folders_repo=self.folders_repo,
            folder_id=folder_id,
        )
        dialog.sig_folder_removed.connect(
            lambda: self.collections_tree.delete_folder_by_id(folder_id)
        )
        dialog.sig_folder_removed.connect(self.top_bar_area.update_tabs)
        dialog.exec()

    # TODO: Try Request(**get_data())
    def get_request(self) -> Request:
        method = self.url_area.get_data()['method']
        url = self.url_area.get_data()['url']

        headers = [
            Request.Header(
                enabled=header['enabled'],
                key=header['key'],
                value=header['value'],
            )
            for header in self.request_area.get_data()['headers']
        ]

        params = [
            Request.Param(
                enabled=param['enabled'],
                key=param['key'],
                value=param['value'],
            )
            for param in self.request_area.get_data()['params']
        ]

        auth_enabled = self.request_area.get_data()['auth_enabled']
        auth_mode = self.request_area.get_data()['auth_mode']
        auth = None
        if auth_mode == AuthMode.BASIC:
            auth = Request.BasicAuth(
                username=self.request_area.get_data()['auth']['username'],
                password=self.request_area.get_data()['auth']['password'],
            )
        elif auth_mode == AuthMode.BEARER:
            auth = Request.BearerAuth(
                token=self.request_area.get_data()['auth']['token']
            )
        elif auth_mode == AuthMode.API_KEY:
            auth = Request.ApiKeyAuth(
                key=self.request_area.get_data()['auth']['key'],
                value=self.request_area.get_data()['auth']['value'],
                where=self.request_area.get_data()['auth']['where'],
            )
        elif auth_mode == AuthMode.DIGEST:
            auth = Request.DigestAuth(
                username=self.request_area.get_data()['username'],
                password=self.request_area.get_data()['password'],
            )

        body_enabled = self.request_area.get_data()['body_enabled']
        body_mode = self.request_area.get_data()['body_mode']
        body = None
        if body_mode == BodyMode.RAW:
            body = Request.RawBody(
                language=BodyRawLanguage(
                    self.request_area.get_data()['body']['language']
                ),
                value=self.request_area.get_data()['body']['value'],
            )
        elif body_mode == BodyMode.FILE:
            body = Request.FileBody(
                file=self.request_area.get_data()['body']['file']
            )
        elif body_mode == BodyMode.FORM_URLENCODED:
            body = Request.UrlEncodedFormBody(
                fields=[
                    Request.UrlEncodedFormBody.Field(
                        enabled=form_field['enabled'],
                        key=form_field['key'],
                        value=form_field['value'],
                    )
                    for form_field in self.request_area.get_data()['body'][
                        'fields'
                    ]
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
                    for form_field in self.request_area.get_data()['body'][
                        'fields'
                    ]
                ]
            )

        options = Request.Options(
            timeout=self.request_area.get_data()['options']['timeout'],
            follow_redirects=self.request_area.get_data()['options'][
                'follow_redirects'
            ],
            verify_ssl=self.request_area.get_data()['options']['verify_ssl'],
            attach_cookies=self.request_area.get_data()['options'][
                'attach_cookies'
            ],
        )

        return Request(
            id=self._selected_request.id,
            folder_id=self._selected_request.folder_id,
            name=self._selected_request.name,
            method=method,
            url=url,
            headers=headers,
            params=params,
            body_enabled=body_enabled,
            body_mode=body_mode,
            body=body,
            auth_enabled=auth_enabled,
            auth_mode=auth_mode,
            auth=auth,
            options=options,
            created_at=self._selected_request.created_at,
            updated_at=self._selected_request.updated_at,
        )

    def get_resolved_request(self) -> Request:
        global_environment = self.environments_repo.get_by_name(
            name='global'
        ).data
        resolved_global_environment = global_environment.resolve_variables()
        request = self.get_request().resolve_variables(
            resolved_global_environment.variables
        )
        if self.top_bar_area.get_data()['environment_name']:
            environment = self.environments_repo.get_by_name(
                name=self.top_bar_area.get_data()['environment_name']
            ).data
            resolved_environment = environment.resolve_variables()
            request = request.resolve_variables(resolved_environment.variables)
        return request

    # TODO: Try model_dump()
    def set_request(self, request: Request) -> None:
        self.url_area.clear_data()
        self.request_area.clear_data()

        self.url_area.set_data({'method': request.method, 'url': request.url})
        request_area_data = {
            'headers': [
                {
                    'enabled': header.enabled,
                    'key': header.key,
                    'value': header.value,
                }
                for header in request.headers
            ],
            'params': [
                {
                    'enabled': param.enabled,
                    'key': param.key,
                    'value': param.value,
                }
                for param in request.params
            ],
            'auth_enabled': request.auth_enabled,
            'auth_mode': request.auth_mode,
            'body_enabled': request.body_enabled,
            'body_mode': request.body_mode,
            'options': {
                'timeout': request.options.timeout,
                'follow_redirects': request.options.follow_redirects,
                'verify_ssl': request.options.verify_ssl,
                'attach_cookies': request.options.attach_cookies,
            },
        }

        if request.auth_mode == AuthMode.BASIC:
            request_area_data['auth'] = {
                'username': request.auth.username,
                'password': request.auth.password,
            }
        elif request.auth_mode == AuthMode.BEARER:
            request_area_data['auth'] = {'token': request.auth.token}
        elif request.auth_mode == AuthMode.API_KEY:
            request_area_data['auth'] = {
                'where': request.auth.where,
                'key': request.auth.key,
                'value': request.auth.value,
            }
        elif request.auth_mode == AuthMode.DIGEST:
            request_area_data['auth'] = {
                'username': request.auth.username,
                'password': request.auth.password,
            }

        if request.body_mode == BodyMode.RAW:
            request_area_data['body'] = {
                'language': request.body.language,
                'value': request.body.value,
            }
        elif request.body_mode == BodyMode.FILE:
            request_area_data['body'] = {'file': request.body.file}
        elif request.body_mode == BodyMode.FORM_URLENCODED:
            request_area_data['body'] = {
                'fields': [
                    {
                        'enabled': field.enabled,
                        'key': field.key,
                        'value': field.value,
                    }
                    for field in request.body.fields
                ]
            }
        elif request.body_mode == BodyMode.FORM_MULTIPART:
            request_area_data['body'] = {
                'fields': [
                    {
                        'value_kind': field.value_kind,
                        'enabled': field.enabled,
                        'key': field.key,
                        'value': field.value,
                    }
                    for field in request.body.fields
                ]
            }
        self.request_area.set_data(request_area_data)

    async def _send_request(self, download: bool = False) -> None:
        self.response_area.clear_data()
        self.response_area.is_loading = True
        self.url_area.request_pending = True

        try:
            request = self.get_resolved_request()

            async with httpx.AsyncClient(
                timeout=request.options.timeout,
                follow_redirects=request.options.follow_redirects,
                verify=request.options.verify_ssl,
                cookies=self._cookies
                if request.options.attach_cookies
                else None,
            ) as http_client:
                response = await http_client.send(
                    request=request.to_httpx_req(httpx_client=http_client),
                    auth=request.to_httpx_auth(),
                )

            if request.options.attach_cookies:
                self._cookies.extract_cookies(response)

            if download:
                self._download_response(response=response)

            self._display_response(response=response)
            self.response_area.show_response()
            self._request_id_to_response[request.id] = response

        except httpx.RequestError as error:
            error_name = type(error).__name__
            error_message = str(error)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Request error')
            if error_message:
                msg.setText(f'{error_name}: {error_message}')
            else:
                msg.setText(f'{error_name}')
            msg.exec()
            self.response_area.clear_data()
            self.response_area.show_empty()

        except asyncio.CancelledError:
            self.response_area.clear_data()
            self.response_area.show_empty()

        finally:
            self.response_area.is_loading = False
            self.url_area.request_pending = False

    def _download_response(self, response: httpx.Response) -> None:
        content_disposition = response.headers.get('content-disposition')
        if content_disposition and 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"')
        else:
            filename = (
                response.url.path.removeprefix('/')
                .removesuffix('/')
                .replace('/', '-')
                or 'response'
            )
        filename = filename.rsplit('.', 1)[0]

        content_type = response.headers.get('content-type')
        if content_type:
            filesuffix = (
                mimetypes.guess_extension(content_type.split(';')[0]) or '.bin'
            )
        else:
            filesuffix = '.bin'

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Response',
            f'{filename}{filesuffix}',
            f'*{filesuffix}',
        )

        if not file_path:
            return

        file = Path(file_path)
        try:
            file.write_bytes(response.content)
        except OSError as error:
            QMessageBox.critical(
                self, 'Save Response', f'Could not save file:\n{error}'
            )
            return

        QMessageBox.information(self, 'Save Response', f'File saved:\n{file}')

    def _display_response(self, response: httpx.Response) -> None:
        content_type_to_body_language = {
            ContentType.TEXT: BodyRawLanguage.PLAIN,
            ContentType.HTML: BodyRawLanguage.HTML,
            ContentType.JSON: BodyRawLanguage.JSON,
            ContentType.YAML: BodyRawLanguage.YAML,
            ContentType.XML: BodyRawLanguage.XML,
        }

        content_type = response.headers.get('Content-Type', '')
        mimetype = content_type.split(';', 1)[0].strip().lower()

        response_data = {
            'status': HTTPStatus(response.status_code),
            'content_size': response.num_bytes_downloaded,
            'elapsed_time': round(response.elapsed.total_seconds(), 2),
            'headers': {
                header_key: header_value
                for header_key, header_value in response.headers.multi_items()
            },
        }
        response_data['body_raw_language'] = content_type_to_body_language.get(
            mimetype, BodyRawLanguage.PLAIN
        )
        if response_data['body_raw_language'] == BodyRawLanguage.JSON:
            try:
                response_data['body_raw'] = json.dumps(
                    json.loads(response.text),
                    ensure_ascii=False,
                    indent=2,
                )
                self.response_area.set_data(response_data)
                return
            except json.JSONDecodeError:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setText(
                    'Content-Type is JSON, but the response body is not valid JSON'
                )
                msg.exec()

        if _is_textual_mimetype(mimetype=mimetype):
            response_data['body_raw'] = response.text
        else:
            response_data['body_raw'] = (
                '[BINARY CONTENT]\nPress "Download" to save'
            )

        self.response_area.set_data(response_data)


class RenameFolderDialog(QDialog):
    sig_folder_renamed = Signal(Folder)

    def __init__(
        self, parent: QWidget, folders_repo: RequestsSQLRepo, folder_id: int
    ) -> None:
        super().__init__(parent)
        self.folders_repo = folders_repo
        self.folder_id = folder_id
        self.folder = self.folders_repo.get_by_id(id=folder_id).data

        self.setWindowTitle('Rename folder')
        self.resize(400, 100)

        self.name_label = QLabel('Name')
        self.name_input = QLineEdit()
        self.name_input.setText(self.folder.name)

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.name_label)
        first_row.addWidget(self.name_input)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        resp = self.folders_repo.update(
            folder=self.folder.model_copy(
                update={'name': self.name_input.text()}
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to rename folder ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
        folder = resp.data

        self.sig_folder_renamed.emit(folder)
        self.accept()


class RenameRequestDialog(QDialog):
    sig_request_renamed = Signal(Request)

    def __init__(
        self, parent: QWidget, requests_repo: RequestsSQLRepo, request_id: int
    ) -> None:
        super().__init__(parent)
        self.requests_repo = requests_repo
        self.request_id = request_id
        self.request = self.requests_repo.get_by_id(id=request_id).data

        self.setWindowTitle('Rename request')
        self.resize(400, 100)

        self.name_label = QLabel('Name')
        self.name_input = QLineEdit()
        self.name_input.setText(self.request.name)

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.name_label)
        first_row.addWidget(self.name_input)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        resp = self.requests_repo.update(
            request=self.request.model_copy(
                update={'name': self.name_input.text()}
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to rename request ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
        request = resp.data

        self.sig_request_renamed.emit(request)
        self.accept()


class AddRequestDialog(QDialog):
    sig_request_added = Signal(Request)

    def __init__(
        self,
        parent: QWidget,
        requests_repo: RequestsSQLRepo,
        parent_folder_id: int,
    ) -> None:
        super().__init__(parent)
        self.requests_repo = requests_repo
        self.parent_folder_id = parent_folder_id

        self.setWindowTitle('Add request')
        self.resize(400, 100)

        self.name_label = QLabel('Name')
        self.name_input = QLineEdit()

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.name_label)
        first_row.addWidget(self.name_input)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        resp = self.requests_repo.create(
            request=Request(
                folder_id=self.parent_folder_id, name=self.name_input.text()
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to create request ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
        request = resp.data

        self.sig_request_added.emit(request)
        self.accept()


class RemoveRequestDialog(QDialog):
    sig_request_removed = Signal()

    def __init__(
        self, parent: QWidget, requests_repo: FoldersSQLRepo, request_id: int
    ) -> None:
        super().__init__(parent)
        self.requests_repo = requests_repo
        self.request_id = request_id

        self.setWindowTitle('Remove request')
        self.resize(400, 100)

        self.are_you_sure_label = QLabel()
        self.are_you_sure_label.setText('Are you sure?')
        self.are_you_sure_label.setAlignment(Qt.AlignCenter)

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.are_you_sure_label)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        resp = self.requests_repo.delete_by_id(id=self.request_id)
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to delete folder ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        self.sig_request_removed.emit()
        self.accept()


class RemoveFolderDialog(QDialog):
    sig_folder_removed = Signal()

    def __init__(
        self, parent: QWidget, folders_repo: FoldersSQLRepo, folder_id: int
    ) -> None:
        super().__init__(parent)
        self.folders_repo = folders_repo
        self.folder_id = folder_id

        self.setWindowTitle('Remove folder')
        self.resize(400, 100)

        self.are_you_sure_label = QLabel()
        self.are_you_sure_label.setText('Are you sure?')
        self.are_you_sure_label.setAlignment(Qt.AlignCenter)

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.are_you_sure_label)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        resp = self.folders_repo.delete_by_id(id=self.folder_id)
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to delete folder ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return

        self.sig_folder_removed.emit()
        self.accept()


class AddFolderDialog(QDialog):
    sig_folder_added = Signal(Folder)

    def __init__(
        self,
        parent: QWidget,
        parent_folder_id: int,
        folders_repo: FoldersSQLRepo,
    ) -> None:
        super().__init__(parent)
        self.parent_folder_id = parent_folder_id
        self.folders_repo = folders_repo

        self.setWindowTitle('Add folder')
        self.resize(400, 100)

        self.name_label = QLabel('Name')
        self.name_input = QLineEdit()

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')
        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.name_label)
        first_row.addWidget(self.name_input)

        second_row = QHBoxLayout()
        second_row.addStretch()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addStretch()
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        resp = self.folders_repo.create(
            folder=Folder(
                parent_id=self.parent_folder_id, name=self.name_input.text()
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to create folder ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
        folder = resp.data

        self.sig_folder_added.emit(folder)
        self.accept()


class MoveRequestDialog(QDialog):
    sig_request_moved = Signal(Request)

    def __init__(
        self,
        parent: QWidget,
        requests_repo: RequestsSQLRepo,
        folders_repo: FoldersSQLRepo,
        request_id: int,
        folder_id: int,
    ) -> None:
        super().__init__(parent)
        self.requests_repo = requests_repo
        self.folders_repo = folders_repo
        self.request_id = request_id
        self.folder_id = folder_id

        self.setWindowTitle('Move request')
        self.resize(400, 100)

        self.path_label = QLabel()
        self.path_label.setText('Path')
        self.path_combo_box = QComboBox()
        for folder in _resolve_all_folder_paths(
            folders_repo=self.folders_repo
        ):
            self.path_combo_box.addItem(folder['path'], folder['id'])
        idx = self.path_combo_box.findData(str(self.folder_id))
        if idx != -1:
            self.path_combo_box.setCurrentIndex(idx)

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')

        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.path_label)
        first_row.addWidget(self.path_combo_box, 1)

        second_row = QHBoxLayout()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        request = self.requests_repo.get_by_id(id=self.request_id).data
        resp = self.requests_repo.update(
            request.model_copy(
                update={'folder_id': self.path_combo_box.currentData()}
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to move request ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
        request = resp.data

        self.sig_request_moved.emit(request)
        self.accept()


class MoveFolderDialog(QDialog):
    sig_folder_moved = Signal(Folder)

    def __init__(
        self,
        parent: QWidget,
        folders_repo: FoldersSQLRepo,
        folder_id: int,
        parent_id: int,
    ) -> None:
        super().__init__(parent)
        self.folders_repo = folders_repo
        self.folder_id = folder_id
        self.parent_id = parent_id

        self.setWindowTitle('Move folder')
        self.resize(400, 100)

        self.path_label = QLabel()
        self.path_label.setText('Path')
        self.path_combo_box = QComboBox()
        for folder in _resolve_all_folder_paths(
            folders_repo=self.folders_repo
        ):
            if folder['id'] == self.folder_id:
                continue
            self.path_combo_box.addItem(folder['path'], folder['id'])
        idx = self.path_combo_box.findData(str(self.parent_id))
        if idx != -1:
            self.path_combo_box.setCurrentIndex(idx)

        self.cancel_button = QPushButton()
        self.cancel_button.setText('Cancel')

        self.confirm_button = QPushButton()
        self.confirm_button.setText('Confirm')

        first_row = QHBoxLayout()
        first_row.addWidget(self.path_label)
        first_row.addWidget(self.path_combo_box, 1)

        second_row = QHBoxLayout()
        second_row.addWidget(self.cancel_button)
        second_row.addWidget(self.confirm_button)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addLayout(second_row)

        self.cancel_button.clicked.connect(self._on_cancel)
        self.confirm_button.clicked.connect(self._on_confirm)

    def _on_cancel(self) -> None:
        self.reject()

    def _on_confirm(self) -> None:
        folder = self.folders_repo.get_by_id(id=self.folder_id).data
        resp = self.folders_repo.update(
            folder.model_copy(
                update={'parent_id': self.path_combo_box.currentData()}
            )
        )
        if not resp.ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f'Failed to move folder ({resp.status})')
            msg.setWindowTitle('Error')
            msg.exec()
            return
        folder = resp.data

        self.sig_folder_moved.emit(folder)
        self.accept()


def _resolve_all_folder_paths(
    folders_repo: FoldersSQLRepo,
) -> list[dict[str, str | int | None]]:
    paths: list[dict[str, str | int | None]] = [{'path': '/', 'id': None}]

    paths_stack: list[tuple[str, int | None]] = [('/', None)]
    while paths_stack:
        parent_path, parent_id = paths_stack.pop(0)

        if parent_id is None:
            children = folders_repo.get_roots().data
        else:
            children = folders_repo.get_by_parent_id(parent_id).data

        for folder in children:
            path = f'{parent_path.rstrip("/")}/{folder.name}'
            paths.append({'path': path, 'id': folder.id})
            paths_stack.append((path, folder.id))

    ordered_paths = sorted(paths, key=lambda x: x['path'].lower())

    return ordered_paths
