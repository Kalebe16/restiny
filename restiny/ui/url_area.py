from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, ContentSwitcher, Select, Static

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
        border: heavy black;
        border-title-color: gray;
    }
    """

    class SendRequest(Message):
        """
        Sent when the user send a request.
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
                id='request-button-switcher', initial='send-request'
            ):
                yield Button(
                    label='Send Request',
                    id='send-request',
                    classes='w-1fr',
                    variant='default',
                )
                yield Button(
                    label='Cancel Request',
                    id='cancel-request',
                    classes='w-1fr',
                    variant='error',
                )

    def on_mount(self) -> None:
        self._request_button_switcher = self.query_one(
            '#request-button-switcher', ContentSwitcher
        )

        self.method_select = self.query_one('#method', Select)
        self.url_input = self.query_one('#url', CustomInput)
        self.send_request_button = self.query_one('#send-request', Button)
        self.cancel_request_button = self.query_one('#cancel-request', Button)

    @property
    def request_pending(self) -> bool:
        return self._request_pending

    @request_pending.setter
    def request_pending(self, value: bool) -> None:
        if value is True:
            self._request_button_switcher.current = 'cancel-request'
        elif value is False:
            self._request_button_switcher.current = 'send-request'

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

    @on(Button.Pressed, '#send-request')
    @on(CustomInput.Submitted, '#url')
    def _on_send_request(
        self, message: Button.Pressed | CustomInput.Submitted
    ) -> None:
        if self.request_pending:
            return

        self.post_message(message=self.SendRequest())

    @on(Button.Pressed, '#cancel-request')
    @on(CustomInput.Submitted, '#url')
    def _on_cancel_request(self, message: Button.Pressed) -> None:
        if not self.request_pending:
            return

        self.post_message(message=self.CancelRequest())
