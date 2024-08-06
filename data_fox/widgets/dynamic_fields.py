import asyncio

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Button, Input, Static, Switch


class DynamicField(Static):
    """
    Enableable and removable field
    """

    DEFAULT_CSS = """
    DynamicField {
        layout: grid;
        grid-size: 4 1;
        grid-columns: auto 1fr 2fr auto; /* Set 1:2 ratio between Inputs */
    }
    """

    class Enabled(Message):
        """
        Sent when the user enables the field.
        """

        def __init__(self, field_enabled: 'DynamicField') -> None:
            super().__init__()
            self.field_enabled = field_enabled

    class Disabled(Message):
        """
        Sent when the user disables the field.
        """

        def __init__(self, field_disabled: 'DynamicField') -> None:
            super().__init__()
            self.field_disabled = field_disabled

    class RemoveRequested(Message):
        """
        Sent when the user clicks the remove button.
        The listener of this event decides whether to actually remove the field or not.
        """

        def __init__(self, field_to_remove: 'DynamicField') -> None:
            super().__init__()
            self.field_to_remove = field_to_remove

    def __init__(
        self, enabled: bool, key: str, value: str, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        # Store initial values temporarily; applied after mounting.
        self._initial_enabled = enabled
        self._initial_key = key
        self._initial_value = value

    def compose(self) -> ComposeResult:
        yield Switch(value=False, tooltip='Send this field?')
        yield Input(placeholder='Key', id='input-key')
        yield Input(placeholder='Value', id='input-value')
        yield Button(label='➖', tooltip='Remove field')

    def on_mount(self) -> None:
        # Link UI elements.
        self.enabled_switch: Switch = self.query_one(Switch)
        self.key_input: Input = self.query_one('#input-key')
        self.value_input: Input = self.query_one('#input-value')
        self.remove_button: Button = self.query_one(Button)

        # Apply stored initial values.
        self.enabled = self._initial_enabled
        self.key = self._initial_key
        self.value = self._initial_value

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

    @on(Switch.Changed)
    def on_enabled_or_disabled(self, message: Switch.Changed) -> None:
        if message.value is True:
            self.post_message(self.Enabled(field_enabled=self))
        elif message.value is False:
            self.post_message(message=self.Disabled(field_disabled=self))
        message.stop()

    @on(Button.Pressed)
    def on_remove_requested(self, message: Button.Pressed) -> None:
        self.post_message(self.RemoveRequested(field_to_remove=self))
        message.stop()


class DynamicFields(Static):
    """
    Enableable and removable fields
    """

    def __init__(self, fields: list[DynamicField], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._initial_fields = fields

    def compose(self) -> ComposeResult:
        yield VerticalScroll()
        yield Button(label='➕', tooltip='Add field', classes='w-full')

    async def on_mount(self) -> None:
        self.fields_container = self.query_one(VerticalScroll)
        self.add_field_button = self.query_one(Button)

        # Set initial_fields
        for field in self._initial_fields:
            await self.add_field(field=field)

    @property
    def fields(self) -> list[DynamicField]:
        return list(self.query(DynamicField))

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

    @on(Button.Pressed)
    async def on_add_field_requested(self, message: Button.Pressed) -> None:
        await self.add_field(
            field=DynamicField(enabled=False, key='', value='')
        )
        message.stop()

    @on(DynamicField.RemoveRequested)
    async def on_remove_field_requested(
        self, message: DynamicField.RemoveRequested
    ) -> None:
        await self.remove_field(field=message.field_to_remove)
        message.stop()

    async def add_field(self, field: DynamicField) -> None:
        await self.fields_container.mount(field)

    async def remove_field(self, field: DynamicField) -> None:
        if len(self.fields) == 1:
            self.app.bell()
            return

        field.add_class('hidden')
        self.fields[self.fields.index(field) - 1].remove_button.focus()
        await field.remove()
