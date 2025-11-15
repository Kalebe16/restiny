from abc import abstractmethod
from enum import StrEnum
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    Button,
    ContentSwitcher,
    RadioButton,
    RadioSet,
    Switch,
)

from restiny.widgets import CustomInput
from restiny.widgets.path_chooser import PathChooser


class DynamicField(Widget):
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
        width: 100%;
        height: auto;
        layout: grid;
        grid-size: 4 1;
        grid-columns: auto 1fr 2fr auto; /* Set 1:2 ratio between Inputs */
    }
    """

    def __init__(
        self, enabled: bool, key: str, value: str, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._enabled = enabled
        self._key = key
        self._value = value

    def compose(self) -> ComposeResult:
        yield Switch(
            value=self._enabled,
            tooltip='Send this field?',
            id='enabled',
        )
        yield CustomInput(
            value=self._key,
            placeholder='Key',
            select_on_focus=False,
            id='key',
        )
        yield CustomInput(
            value=self._value,
            placeholder='Value',
            select_on_focus=False,
            id='value',
        )
        yield Button(label='➖', tooltip='Remove field', id='remove')

    async def on_mount(self) -> None:
        self.enabled_switch = self.query_one('#enabled', Switch)
        self.key_input = self.query_one('#key', CustomInput)
        self.value_input = self.query_one('#value', CustomInput)
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

    @on(Switch.Changed, '#enabled')
    def on_enabled_or_disabled(self, message: Switch.Changed) -> None:
        if message.value is True:
            self.post_message(self.Enabled(field=self))
        elif message.value is False:
            self.post_message(message=self.Disabled(field=self))

    @on(CustomInput.Changed, '#key')
    @on(CustomInput.Changed, '#value')
    def on_input_changed(self, message: CustomInput.Changed) -> None:
        if self.is_empty:
            self.post_message(message=self.Empty(field=self))
        elif self.is_filled:
            self.post_message(message=self.Filled(field=self))

    @on(Button.Pressed, '#remove')
    def on_remove_requested(self, message: Button.Pressed) -> None:
        self.post_message(self.RemoveRequested(field=self))


class _ValueKind(StrEnum):
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
        value_kind: _ValueKind = _ValueKind.TEXT,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._enabled = enabled
        self._key = key
        self._value = value
        self._value_kind = value_kind

    def compose(self) -> ComposeResult:
        with RadioSet(id='value-kind', compact=True):
            yield RadioButton(
                label=_ValueKind.TEXT,
                value=bool(self._value_kind == _ValueKind.TEXT),
                id='value-kind-text',
            )
            yield RadioButton(
                label=_ValueKind.FILE,
                value=bool(self._value_kind == _ValueKind.FILE),
                id='value-kind-file',
            )
        yield Switch(
            value=self._enabled,
            tooltip='Send this field?',
            id='enabled',
        )
        yield CustomInput(
            value=self._key,
            placeholder='Key',
            select_on_focus=False,
            id='key',
        )
        with ContentSwitcher(
            initial='value-text'
            if self._value_kind == _ValueKind.TEXT
            else 'value-file',
            id='value-kind-switcher',
        ):
            yield CustomInput(
                value=self._value
                if self._value_kind == _ValueKind.TEXT
                else '',
                placeholder='Value',
                select_on_focus=False,
                id='value-text',
            )
            yield PathChooser.file(
                path=self._value
                if self._value_kind == _ValueKind.FILE
                else None,
                id='value-file',
            )
        yield Button(label='➖', tooltip='Remove field', id='remove')

    def on_mount(self) -> None:
        self.value_kind_switcher = self.query_one(
            '#value-kind-switcher', ContentSwitcher
        )

        self.value_kind_radioset = self.query_one('#value-kind', RadioSet)
        self.value_kind_text_radio_button = self.query_one(
            '#value-kind-text', RadioButton
        )
        self.value_kind_file_radio_button = self.query_one(
            '#value-kind-file', RadioButton
        )
        self.enabled_switch = self.query_one('#enabled', Switch)
        self.key_input = self.query_one('#key', CustomInput)
        self.value_text_input = self.query_one('#value-text', CustomInput)
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
        if self.value_kind == _ValueKind.TEXT:
            return self.value_text_input.value
        elif self.value_kind == _ValueKind.FILE:
            return self.value_file_input.path

    @value.setter
    def value(self, value: str | Path | None) -> None:
        if isinstance(value, str):
            self.value_text_input.value = value
        elif isinstance(value, Path) or value is None:
            self.value_file_input.path = value

    @property
    def value_kind(self) -> _ValueKind:
        return _ValueKind(self.value_kind_radioset.pressed_button.label)

    @value_kind.setter
    def value_kind(self, value: _ValueKind) -> None:
        if value == _ValueKind.TEXT:
            self.value_kind_switcher.current = 'value-text'
            self.value_kind_text_radio_button.value = True
        elif value == _ValueKind.FILE:
            self.value_kind_switcher.current = 'value-file'
            self.value_kind_file_radio_button.value = True

    @property
    def is_filled(self) -> bool:
        if len(self.key_input.value) > 0:
            return True
        elif (
            self.value_kind == _ValueKind.TEXT
            and len(self.value_text_input.value) > 0
        ):
            return True
        elif (
            self.value_kind == _ValueKind.FILE
            and self.value_file_input.path is not None
        ):
            return True
        else:
            return False

    @property
    def is_empty(self) -> bool:
        return not self.is_filled

    @on(RadioSet.Changed, '#value-kind')
    def on_value_kind_changed(self, message: RadioSet.Changed) -> None:
        self.value_kind = _ValueKind(message.pressed.label)

    @on(Switch.Changed, '#enabled')
    def on_enabled_or_disabled(self, message: Switch.Changed) -> None:
        if message.value is True:
            self.post_message(self.Enabled(field=self))
        elif message.value is False:
            self.post_message(message=self.Disabled(field=self))

    @on(CustomInput.Changed, '#key')
    @on(CustomInput.Changed, '#value-text')
    @on(PathChooser.Changed, '#value-file')
    def on_input_changed(
        self, message: CustomInput.Changed | PathChooser.Changed
    ) -> None:
        if self.is_empty:
            self.post_message(message=self.Empty(field=self))
        elif self.is_filled:
            self.post_message(message=self.Filled(field=self))

    @on(Button.Pressed, '#remove')
    def on_remove_requested(self, message: Button.Pressed) -> None:
        self.post_message(self.RemoveRequested(field=self))


class DynamicFields(Widget):
    """
    Enableable and removable fields
    """

    DEFAULT_CSS = """
    DynamicFields {
        width: auto;
        height: 1fr;
    }
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
        with VerticalScroll(can_focus=False):
            yield from self._fields

    def on_mount(self) -> None:
        self.fields_container = self.query_one(VerticalScroll)

    @property
    def fields(self) -> list[DynamicField]:
        return list(self.query(DynamicField))

    @property
    def empty_fields(self) -> list[DynamicField]:
        return [field for field in self.fields if field.is_empty]

    @property
    def filled_fields(self) -> list[DynamicField]:
        return [field for field in self.fields if field.is_filled]

    async def add_field(
        self, field: DynamicField, before_last: bool = False
    ) -> None:
        if before_last:
            await self.fields_container.mount(field, before=self.fields[-1])
        else:
            await self.fields_container.mount(field)

    def remove_field(
        self, field: DynamicField, focus_neighbor: bool = False
    ) -> None:
        if len(self.fields) == 1:
            self.app.bell()
            return
        elif field is self.fields[-1]:
            self.app.bell()
            return

        if focus_neighbor:
            field_index = self.fields.index(field)

            neighbor_field = None
            if field_index == 0:
                neighbor_field = self.fields[field_index + 1]
            else:
                neighbor_field = self.fields[field_index - 1]

            self.app.set_focus(neighbor_field.query_one(CustomInput))

        field.add_class('hidden')
        field.remove()

    @on(DynamicField.Empty)
    def _on_field_is_empty(self, message: DynamicField.Empty) -> None:
        self.remove_field(field=message.field, focus_neighbor=True)
        self.post_message(
            message=self.FieldEmpty(fields=self, field=message.field)
        )

    @on(DynamicField.Filled)
    async def _on_field_is_filled(self, message: DynamicField.Filled) -> None:
        if len(self.empty_fields) == 0:
            field = message.field
            if isinstance(field, TextDynamicField):
                await self.add_field(
                    TextDynamicField(enabled=False, key='', value='')
                )
            elif isinstance(field, TextOrFileDynamicField):
                await self.add_field(
                    TextOrFileDynamicField(
                        enabled=False,
                        key='',
                        value='',
                        value_kind=_ValueKind.TEXT,
                    )
                )

        self.post_message(
            message=self.FieldFilled(fields=self, field=message.field)
        )

    @on(DynamicField.RemoveRequested)
    def _on_field_remove_requested(
        self, message: DynamicField.RemoveRequested
    ) -> None:
        self.remove_field(field=message.field, focus_neighbor=True)
