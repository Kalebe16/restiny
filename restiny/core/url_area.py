from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Button, ContentSwitcher, Input, Select, Static

from restiny.enums import HTTPMethod


@dataclass
class URLAreaData:
    method: str
    url: str


class URLArea(Static):
    ALLOW_MAXIMIZE = True
    focusable = True
    BORDER_TITLE = 'URL'
    DEFAULT_CSS = """
    URLArea {
        layout: grid;
        grid-size: 3 1;
        grid-columns: 1fr 6fr 1fr;
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
        yield Select.from_values(
            values=HTTPMethod.values(), allow_blank=False, id='method'
        )
        yield Input(placeholder='Enter URL', select_on_focus=False, id='url')
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
        self.url_input = self.query_one('#url', Input)
        self.send_request_button = self.query_one('#send-request', Button)
        self.cancel_request_button = self.query_one('#cancel-request', Button)

    def get_data(self) -> URLAreaData:
        return URLAreaData(
            method=self.method_select.value,
            url=self.url_input.value,
        )

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

    @on(Button.Pressed, '#send-request')
    @on(Input.Submitted, '#url')
    def _on_send_request(
        self, message: Button.Pressed | Input.Submitted
    ) -> None:
        if self.request_pending:
            return

        self.post_message(message=self.SendRequest())

    @on(Button.Pressed, '#cancel-request')
    @on(Input.Submitted, '#url')
    def _on_cancel_request(self, message: Button.Pressed) -> None:
        if not self.request_pending:
            return

        self.post_message(message=self.CancelRequest())
