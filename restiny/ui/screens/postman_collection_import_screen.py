import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button

from restiny.entities import Folder, Request
from restiny.enums import AuthMode, BodyMode, BodyRawLanguage
from restiny.widgets import PathChooser

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class _ImportInvalidVersionError(Exception):
    pass


class _ImportFailedError(Exception):
    pass


class _ImportInvalidFileError(Exception):
    pass


class PostmanCollectionImportScreen(ModalScreen):
    app: 'RESTinyApp'

    DEFAULT_CSS = """
    PostmanCollectionImportScreen {
        align: center middle;
    }

    #modal-content {
        width: 30%;
        height: auto;
        border: heavy black;
        border-title-color: gray;
        background: $surface;
    }

    Label {
        margin-left: 4;
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
                yield PathChooser.file(id='collection-file')
            with Horizontal(classes='w-auto h-auto'):
                yield Button('Cancel', classes='w-1fr', id='cancel')
                yield Button('Confirm', classes='w-1fr', id='confirm')

    def on_mount(self) -> None:
        self.modal_content = self.query_one('#modal-content', Vertical)

        self.collection_file_chooser = self.query_one(
            '#collection-file', PathChooser
        )
        self.cancel_button = self.query_one('#cancel', Button)
        self.confirm_button = self.query_one('#confirm', Button)

        self.modal_content.border_title = 'Postman import'

    @on(Button.Pressed, '#cancel')
    def _on_cancel(self) -> None:
        self.dismiss(result=False)

    @on(Button.Pressed, '#confirm')
    def _on_confirm(self) -> None:
        try:
            self._import()
        except _ImportInvalidFileError:
            self.notify('Invalid collection file', severity='error')
            return
        except _ImportInvalidVersionError:
            self.notify(
                'Invalid collection version (only v2.1 is supported)',
                severity='error',
            )
            return
        except _ImportFailedError:
            self.notify('Failed to import the collection', severity='error')
            return

        self.notify(message='Collection imported', severity='information')
        self.dismiss(result=True)

    def _import(self) -> None:
        try:
            collection = json.loads(
                self.collection_file_chooser.path.read_text()
            )
        except Exception as error:
            raise _ImportInvalidFileError() from error

        if 'v2.1' not in collection['info']['schema']:
            raise _ImportInvalidVersionError()

        with self.app.db_manager.session_scope() as session:
            create_folder_resp = self.app.folders_repo.create(
                folder=Folder(parent_id=None, name=collection['info']['name']),
                session=session,
            )
            if not create_folder_resp.ok:
                raise _ImportFailedError()
            root_folder = create_folder_resp.data

            postman_items_stack = [
                (item, root_folder.id) for item in collection.get('item', [])
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
                    body = None
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
                    auth = None
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

                    create_request_resp = self.app.requests_repo.create(
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
                    create_folder_resp = self.app.folders_repo.create(
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
