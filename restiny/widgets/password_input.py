from enum import StrEnum

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from restiny.widgets import CustomInput


class _Icon(StrEnum):
    SHOW = ' 🔓 '
    HIDE = ' 🔒 '


class _Tooltip(StrEnum):
    SHOW = 'Show'
    HIDE = 'Hide'


class PasswordInput(Widget):
    DEFAULT_CSS = """
    PasswordInput {
        width: 1fr;
        height: auto;
    }

    PasswordInput > Horizontal {
        width: auto;
        height: auto;
    }

    PasswordInput CustomInput {
        width: 1fr;
        margin-right: 0;
        border-right: none;
    }

    PasswordInput CustomInput:focus {
        border-right: none;
    }


    PasswordInput Button {
        width: auto;
        margin-left: 0;
        border-left: none;
    }

    """

    class Changed(Message):
        """
        Sent when value changed.
        """

        def __init__(self, input: 'PasswordInput', value: str):
            super().__init__()
            self.input = input
            self.value = value

        @property
        def control(self) -> 'PasswordInput':
            return self.input

    class Shown(Message):
        """
        Sent when the value becomes visible.
        """

        def __init__(self, input: 'PasswordInput') -> None:
            super().__init__()
            self.input = input

        @property
        def control(self) -> 'PasswordInput':
            return self.input

    class Hidden(Message):
        """
        Sent when the value becomes hidden.
        """

        def __init__(self, input: 'PasswordInput') -> None:
            super().__init__()
            self.input = input

        @property
        def control(self) -> 'PasswordInput':
            return self.input

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            id=kwargs.pop('id', None), classes=kwargs.pop('classes', None)
        )
        kwargs.pop('password', None)
        self._input_args = args
        self._input_kwargs = kwargs

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield CustomInput(
                *self._input_args,
                **self._input_kwargs,
                password=True,
                id='value',
            )
            yield Button(
                _Icon.SHOW, tooltip=_Tooltip.SHOW, id='toggle-visibility'
            )

    def on_mount(self) -> None:
        self.value_input = self.query_one('#value', CustomInput)
        self.toggle_visibility_button = self.query_one(
            '#toggle-visibility', Button
        )

    def show(self) -> None:
        self.value_input.password = False
        self.toggle_visibility_button.label = _Icon.HIDE
        self.toggle_visibility_button.tooltip = _Tooltip.HIDE
        self.post_message(message=self.Hidden(input=self))

    def hide(self) -> None:
        self.value_input.password = True
        self.toggle_visibility_button.label = _Icon.SHOW
        self.toggle_visibility_button.tooltip = _Tooltip.SHOW
        self.post_message(message=self.Shown(input=self))

    @property
    def value(self) -> str:
        return self.value_input.value

    @value.setter
    def value(self, value: str) -> None:
        self.value_input.value = value

    @property
    def shown(self) -> bool:
        return self.value_input.password is False

    @property
    def hidden(self) -> bool:
        return not self.shown

    @on(CustomInput.Changed, '#value')
    def _on_value_changed(self, message: CustomInput.Changed) -> None:
        self.post_message(
            message=self.Changed(input=self, value=message.value)
        )

    @on(Button.Pressed, '#toggle-visibility')
    def _on_toggle_visibility(self, message: Button.Pressed) -> None:
        if self.value_input.password is False:
            self.hide()
        elif self.value_input.password is True:
            self.show()

        self.value_input.focus()
