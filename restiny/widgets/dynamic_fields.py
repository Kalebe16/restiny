from abc import abstractmethod
from enum import StrEnum
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    RadioButton,
    RadioSet,
    Static,
    Switch,
)

from restiny.widgets.path_chooser import PathChooser


class DynamicField(Static):
    @abstractmethod
    def compose(self) -> ComposeResult: ...

    @property
    @abstractmethod
    def enabled(self) -> bool: ...

    @enabled.setter
    @abstractmethod
    def enabled(self, value: bool) -> None: ...

    @property
    @abstractmethod
    def key(self) -> str: ...

    @key.setter
    @abstractmethod
    def key(self, value: str) -> None: ...

    @property
    @abstractmethod
    def value(self) -> str | Path | None: ...

    @value.setter
    @abstractmethod
    def value(self, value: str | Path | None) -> None: ...

    @property
    @abstractmethod
    def is_empty(self) -> bool: ...

    @property
    @abstractmethod
    def is_filled(self) -> bool: ...

    class Enabled(Message):
        """
        Sent when the user enables the field.
        """

        def __init__(self, field: 'DynamicField') -> None:
            super().__init__()
            self.field = field

        @property
        def control(self) -> 'DynamicField':
            return self.field

    class Disabled(Message):
        """
        Sent when the user disables the field.
        """

        def __init__(self, field: 'DynamicField') -> None:
            super().__init__()
            self.field = field

        @property
        def control(self) -> 'DynamicField':
            return self.field

    class Empty(Message):
        """
        Sent when the key input and value input is empty.
        """

        def __init__(self, field: 'DynamicField') -> None:
            super().__init__()
            self.field = field

        @property
        def control(self) -> 'DynamicField':
            return self.field

    class Filled(Message):
        """
        Sent when the key input or value input is filled.
        """

        def __init__(self, field: 'DynamicField') -> None:
            super().__init__()
            self.field = field

        @property
        def control(self) -> 'DynamicField':
            return self.field

    class RemoveRequested(Message):
        """
        Sent when the user clicks the remove button.
        The listener of this event decides whether
        to actually remove the field or not.
        """

        def __init__(self, field: 'DynamicField') -> None:
            super().__init__()
            self.field = field

        @property
        def control(self) -> 'DynamicField':
            return self.field


class TextDynamicField(DynamicField):
    """
    Enableable and removable field
    """

    DEFAULT_CSS = """
    TextDynamicField {
        layout: grid;
        grid-size: 4 1;
        grid-columns: auto 1fr 2fr auto; /* Set 1:2 ratio between Inputs */
    }
    """

    def __init__(
        self, enabled: bool, key: str, value: str, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        # Store initial values temporarily; applied after mounting.
        self._enabled = enabled
        self._key = key
        self._value = value

    def compose(self) -> ComposeResult:
        yield Switch(value=self._enabled, tooltip='Send this field?')
        yield Input(value=self._key, placeholder='Key', id='key')
        yield Input(value=self._value, placeholder='Value', id='value')
        yield Button(label='➖', tooltip='Remove field')

    def on_mount(self) -> None:
        self.enabled_switch: Switch = self.query_one(Switch)
        self.key_input: Input = self.query_one('#key', Input)
        self.value_input: Input = self.query_one('#value', Input)
        self.remove_button: Button = self.query_one(Button)

    @property
    def enabled(self) -> bool:
        return self.enabled_switch.value

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.enabled_switch.value = value

    @property
    def key(self) -> str:
        return self.key_input.value

    @key.setter
    def key(self, value: str) -> None:
        self.key_input.value = value

    @property
    def value(self) -> str:
        return self.value_input.value

    @value.setter
    def value(self, value: str) -> None:
        self.value_input.value = value

    @property
    def is_filled(self) -> bool:
        return len(self.key_input.value) > 0 or len(self.value_input.value) > 0

    @property
    def is_empty(self) -> bool:
        return not self.is_filled

    @on(Switch.Changed)
    def on_enabled_or_disabled(self, message: Switch.Changed) -> None:
        if message.value is True:
            self.post_message(self.Enabled(field=self))
        elif message.value is False:
            self.post_message(message=self.Disabled(field=self))

    @on(Input.Changed)
    def on_input_changed(self, message: Input.Changed) -> None:
        self.enabled_switch.value = True

        if self.is_empty:
            self.post_message(message=self.Empty(field=self))
        elif self.is_filled:
            self.post_message(message=self.Filled(field=self))

    @on(Button.Pressed)
    def on_remove_requested(self, message: Button.Pressed) -> None:
        self.post_message(self.RemoveRequested(field=self))


class _ValueMode(StrEnum):
    TEXT = 'text'
    FILE = 'file'


class TextOrFileDynamicField(DynamicField):
    DEFAULT_CSS = """
    TextOrFileDynamicField {
        width: 100%;
        height: auto;
        layout: grid;
        grid-size: 5 1;
        grid-columns: auto auto 1fr 2fr auto; /* Set 1:2 ratio between Inputs */
    }

    TextOrFileDynamicField > RadioSet > RadioButton.-selected {
        background: $surface;
    }

    TextOrFileDynamicField > ContentSwitcher > PathChooser{
        margin-right: 1;
    }
    """

    def __init__(
        self,
        enabled: bool = False,
        key: str = '',
        value: str | Path | None = '',
        value_mode: _ValueMode = 'text',
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._enabled = enabled
        self._key = key
        self._value = value
        self._value_mode = value_mode

    def compose(self) -> ComposeResult:
        with RadioSet(id='value-mode', compact=True):
            yield RadioButton(
                label=_ValueMode.TEXT,
                value=bool(self._value_mode == _ValueMode.TEXT),
                id='value-mode-text',
            )
            yield RadioButton(
                label=_ValueMode.FILE,
                value=bool(self._value_mode == _ValueMode.FILE),
                id='value-mode-file',
            )
        yield Switch(
            value=self._enabled,
            tooltip='Send this field?',
            id='enabled',
        )
        yield Input(value=self._key, placeholder='Key', id='key')
        with ContentSwitcher(
            initial='value-text'
            if self._value_mode == _ValueMode.TEXT
            else 'value-file',
            id='value-mode-switcher',
        ):
            yield Input(
                value=self._value
                if self._value_mode == _ValueMode.TEXT
                else '',
                placeholder='Value',
                id='value-text',
            )
            yield PathChooser.file(
                path=self._value
                if self._value_mode == _ValueMode.FILE
                else None,
                id='value-file',
            )
        yield Button(label='➖', tooltip='Remove field', id='remove')

    def on_mount(self) -> None:
        self.value_mode_switcher = self.query_one(
            '#value-mode-switcher', ContentSwitcher
        )

        self.value_mode_radioset = self.query_one('#value-mode', RadioSet)
        self.value_mode_text_radio_button = self.query_one(
            '#value-mode-text', RadioButton
        )
        self.value_mode_file_radio_button = self.query_one(
            '#value-mode-file', RadioButton
        )
        self.enabled_switch = self.query_one('#enabled', Switch)
        self.key_input = self.query_one('#key', Input)
        self.value_text_input = self.query_one('#value-text', Input)
        self.value_file_input = self.query_one('#value-file', PathChooser)
        self.remove_button = self.query_one('#remove', Button)

    @property
    def enabled(self) -> bool:
        return self.enabled_switch.value

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.enabled_switch.value = value

    @property
    def key(self) -> str:
        return self.key_input.value

    @key.setter
    def key(self, value: str) -> None:
        self.key_input.value = value

    @property
    def value(self) -> str | Path | None:
        if self.value_mode == _ValueMode.TEXT:
            return self.value_text_input.value
        elif self.value_mode == _ValueMode.FILE:
            return self.value_file_input.path

    @value.setter
    def value(self, value: str | Path) -> None:
        if isinstance(value, str):
            self.value_text_input.value = value
        elif isinstance(value, Path):
            self.value_file_input.path = value

    @property
    def value_mode(self) -> _ValueMode:
        return _ValueMode(self.value_mode_radioset.pressed_button.label)

    @value_mode.setter
    def value_mode(self, value: _ValueMode) -> None:
        if value == _ValueMode.TEXT:
            self.value_mode_switcher.current = 'value-text'
            self.value_mode_text_radio_button.value = True
        elif value == _ValueMode.FILE:
            self.value_mode_switcher.current = 'value-file'
            self.value_mode_file_radio_button.value = True

    @property
    def is_filled(self) -> bool:
        if len(self.key_input.value) > 0:
            return True
        elif (
            self.value_mode == _ValueMode.TEXT
            and len(self.value_text_input.value) > 0
        ):
            return True
        elif (
            self.value_mode == _ValueMode.FILE
            and self.value_file_input.path is not None
        ):
            return True
        else:
            return False

    @property
    def is_empty(self) -> bool:
        return not self.is_filled

    @on(RadioSet.Changed, '#value-mode')
    def on_value_mode_changed(self, message: RadioSet.Changed) -> None:
        self.value_mode = _ValueMode(message.pressed.label)

    @on(Switch.Changed, '#enabled')
    def on_enabled_or_disabled(self, message: Switch.Changed) -> None:
        if message.value is True:
            self.post_message(self.Enabled(field=self))
        elif message.value is False:
            self.post_message(message=self.Disabled(field=self))

    @on(Input.Changed, '#key')
    @on(Input.Changed, '#value-text')
    @on(PathChooser.Changed, '#value-file')
    def on_input_changed(
        self, message: Input.Changed | PathChooser.Changed
    ) -> None:
        self.enabled_switch.value = True

        if self.is_empty:
            self.post_message(message=self.Empty(field=self))
        elif self.is_filled:
            self.post_message(message=self.Filled(field=self))

    @on(Button.Pressed, '#remove')
    def on_remove_requested(self, message: Button.Pressed) -> None:
        self.post_message(self.RemoveRequested(field=self))


class DynamicFields(Static):
    """
    Enableable and removable fields
    """

    class FieldEmpty(Message):
        """
        Sent when one of the fields becomes empty.
        """

        def __init__(
            self, fields: 'DynamicFields', field: DynamicField
        ) -> None:
            super().__init__()
            self.fields = fields
            self.field = field

        @property
        def control(self) -> 'DynamicFields':
            return self.fields

    class FieldFilled(Message):
        """
        Sent when one of the fields becomes filled.
        """

        def __init__(
            self, fields: 'DynamicFields', field: DynamicField
        ) -> None:
            super().__init__()
            self.fields = fields
            self.field = field

        @property
        def control(self) -> 'DynamicFields':
            return self.fields

    def __init__(
        self,
        fields: list[DynamicField],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._fields = fields

    def compose(self) -> ComposeResult:
        yield VerticalScroll()

    async def on_mount(self) -> None:
        self.fields_container = self.query_one(VerticalScroll)

        # Set initial_fields
        for field in self._fields:
            await self.add_field(field=field)

    @property
    def fields(self) -> list[DynamicField]:
        return list(self.query(DynamicField))

    @property
    def empty_fields(self) -> list[DynamicField]:
        return [field for field in self.fields if field.is_empty]

    @property
    def filled_fields(self) -> list[DynamicField]:
        return [field for field in self.fields if field.is_filled]

    @property
    def values(self) -> list[dict[str, str | bool]]:
        return [
            {
                'enabled': field.enabled,
                'key': field.key,
                'value': field.value,
            }
            for field in self.fields
        ]

    @on(DynamicField.Empty)
    async def on_field_is_empty(self, message: DynamicField.Empty) -> None:
        await self.remove_field(field=message.control)
        self.post_message(
            message=self.FieldEmpty(fields=self, field=message.control)
        )

    @on(DynamicField.Filled)
    async def on_field_is_filled(self, message: DynamicField.Filled) -> None:
        if len(self.empty_fields) == 0:
            last_field = self.fields[-1]
            if isinstance(last_field, TextDynamicField):
                await self.add_field(
                    TextDynamicField(enabled=False, key='', value='')
                )
            elif isinstance(last_field, TextOrFileDynamicField):
                await self.add_field(
                    TextOrFileDynamicField(
                        enabled=False,
                        key='',
                        value='',
                        value_mode=_ValueMode.TEXT,
                    )
                )

        self.post_message(
            message=self.FieldFilled(fields=self, field=message.control)
        )

    @on(DynamicField.RemoveRequested)
    async def on_field_remove_requested(
        self, message: DynamicField.RemoveRequested
    ) -> None:
        await self.remove_field(field=message.control)

    async def add_field(self, field: DynamicField) -> None:
        await self.fields_container.mount(field)

    async def remove_field(self, field: DynamicField) -> None:
        if len(self.fields) == 1:
            self.app.bell()
            return
        elif self.fields[-1] is field:  # Last field
            self.app.bell()
            return

        if self.fields[0] is field:  # First field
            self.app.screen.focus_next()
            self.app.screen.focus_next()
            self.app.screen.focus_next()
            self.app.screen.focus_next()
        elif self.fields[-2] is field:  # Penultimate field
            self.app.screen.focus_previous()
            self.app.screen.focus_previous()
            self.app.screen.focus_previous()
            self.app.screen.focus_previous()

        field.add_class('hidden')
        await field.remove()  # Maybe the `await` is unnecessary
