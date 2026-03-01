from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, ContentSwitcher, Rule, Select, Static

from restiny.enums import HTTPMethod
from restiny.widgets import CustomInput


class URLArea(Static):
    ALLOW_MAXIMIZE = True
    focusable = True
    BORDER_TITLE = 'URL'
    DEFAULT_CSS = """
    URLArea {
        width: 1fr;
        height: auto;
        border: heavy $panel;
        border-title-color: $text-muted;
    }
    """

    class SendRequest(Message):
        """
        Sent when the user send a request.
        """

        def __init__(self) -> None:
            super().__init__()

    class DownloadResponse(Message):
        """
        Sent when the user download a response.
        """

        def __init__(self) -> None:
            super().__init__()

    class CancelRequest(Message):
        """
        Sent when the user cancel a request.
        """

        def __init__(self) -> None:
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._request_pending = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes='h-auto'):
            yield Select.from_values(
                values=[method.value for method in HTTPMethod],
                allow_blank=False,
                classes='w-1fr',
                id='method',
            )
            yield CustomInput(
                placeholder='Enter URL',
                select_on_focus=False,
                classes='w-5fr',
                id='url',
            )
            with ContentSwitcher(
                id='request-controls-switcher', initial='request-actions'
            ):
                with Horizontal(classes='h-auto w-auto', id='request-actions'):
                    yield Button(
                        label='Send',
                        id='send',
                        classes='w-1fr',
                        variant='default',
                    )
                    yield Rule(orientation='vertical', classes='h-auto m-0')
                    yield Button(
                        label='Download',
                        id='download',
                        classes='w-1fr',
                        variant='default',
                    )
                yield Button(
                    label='Cancel',
                    id='cancel',
                    classes='w-1fr',
                    variant='error',
                )

    def on_mount(self) -> None:
        self._request_controls_switcher = self.query_one(
            '#request-controls-switcher', ContentSwitcher
        )

        self.method_select = self.query_one('#method', Select)
        self.url_input = self.query_one('#url', CustomInput)
        self.request_actions_container = self.query_one(
            '#request-actions', Horizontal
        )
        self.send_button = self.query_one('#send', Button)
        self.download_button = self.query_one('#download', Button)
        self.cancel_button = self.query_one('#cancel', Button)

    @property
    def request_pending(self) -> bool:
        return self._request_pending

    @request_pending.setter
    def request_pending(self, value: bool) -> None:
        if value is True:
            self._request_controls_switcher.current = 'cancel'
        elif value is False:
            self._request_controls_switcher.current = 'request-actions'

        self._request_pending = value

    @property
    def method(self) -> HTTPMethod:
        return self.method_select.value

    @method.setter
    def method(self, value: HTTPMethod) -> None:
        self.method_select.value = value

    @property
    def url(self) -> str:
        return self.url_input.value

    @url.setter
    def url(self, value: str) -> None:
        self.url_input.value = value

    def clear(self) -> None:
        self.method = HTTPMethod.GET
        self.url = ''

    @on(Button.Pressed, '#send')
    @on(CustomInput.Submitted, '#url')
    def _on_send(
        self, message: Button.Pressed | CustomInput.Submitted
    ) -> None:
        if self.request_pending:
            return

        self.post_message(message=self.SendRequest())

    @on(Button.Pressed, '#download')
    def _on_download(self, message: Button.Pressed) -> None:
        if self.request_pending:
            return

        self.post_message(message=self.DownloadResponse())

    @on(Button.Pressed, '#cancel')
    @on(CustomInput.Submitted, '#url')
    def _on_cancel(self, message: Button.Pressed) -> None:
        if not self.request_pending:
            return

        self.post_message(message=self.CancelRequest())
