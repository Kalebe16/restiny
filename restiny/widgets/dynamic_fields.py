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

        def __init__(self, control: 'DynamicField') -> None:
            super().__init__()
            self._control = control

        def control(self) -> 'DynamicField':
            return self._control

    class Disabled(Message):
        """
        Sent when the user disables the field.
        """

        def __init__(self, control: 'DynamicField') -> None:
            super().__init__()
            self._control = control

        @property
        def control(self) -> 'DynamicField':
            return self._control

    class Empty(Message):
        """
        Sent when the key input and value input is empty.
        """

        def __init__(self, control: 'DynamicField') -> None:
            super().__init__()
            self._control = control

        @property
        def control(self) -> 'DynamicField':
            return self._control

    class Filled(Message):
        """
        Sent when the key input or value input is filled.
        """

        def __init__(self, control: 'DynamicField') -> None:
            super().__init__()
            self._control = control

        @property
        def control(self) -> 'DynamicField':
            return self._control

    class RemoveRequested(Message):
        """
        Sent when the user clicks the remove button.
        The listener of this event decides whether
        to actually remove the field or not.
        """

        def __init__(self, control: 'DynamicField') -> None:
            super().__init__()
            self._control = control

        @property
        def control(self) -> 'DynamicField':
            return self._control

    def __init__(
        self, enabled: bool, key: str, value: str, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        # Store initial values temporarily; applied after mounting.
        self._initial_enabled = enabled
        self._initial_key = key
        self._initial_value = value

    def compose(self) -> ComposeResult:
        yield Switch(value=self._initial_enabled, tooltip='Send this field?')
        yield Input(value=self._initial_key, placeholder='Key', id='input-key')
        yield Input(
            value=self._initial_value, placeholder='Value', id='input-value'
        )
        yield Button(label='➖', tooltip='Remove field')

    def on_mount(self) -> None:
        self.enabled_switch: Switch = self.query_one(Switch)
        self.key_input: Input = self.query_one('#input-key')
        self.value_input: Input = self.query_one('#input-value')
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
    def is_empty(self) -> bool:
        return (
            len(self.key_input.value) == 0 and len(self.value_input.value) == 0
        )

    @property
    def is_filled(self) -> bool:
        return len(self.key_input.value) > 0 or len(self.value_input.value) > 0

    @on(Switch.Changed)
    def on_enabled_or_disabled(self, message: Switch.Changed) -> None:
        if message.value is True:
            self.post_message(self.Enabled(control=self))
        elif message.value is False:
            self.post_message(message=self.Disabled(control=self))

    @on(Input.Changed)
    def on_input_changed(self, message: Input.Changed) -> None:
        self.enabled_switch.value = True

        if self.is_empty:
            self.post_message(message=self.Empty(control=self))
        elif self.is_filled:
            self.post_message(message=self.Filled(control=self))

    @on(Button.Pressed)
    def on_remove_requested(self, message: Button.Pressed) -> None:
        self.post_message(self.RemoveRequested(control=self))


class DynamicFields(Static):
    """
    Enableable and removable fields
    """

    class FieldEmpty(Message):
        """
        Sent when one of the fields becomes empty.
        """

        def __init__(
            self, control: 'DynamicFields', field: DynamicField
        ) -> None:
            super().__init__()
            self._control = control
            self.field = field

        @property
        def control(self) -> 'DynamicFields':
            return self._control

    class FieldFilled(Message):
        """
        Sent when one of the fields becomes filled.
        """

        def __init__(
            self, control: 'DynamicFields', field: DynamicField
        ) -> None:
            super().__init__()
            self._control = control
            self.field = field

        @property
        def control(self) -> 'DynamicFields':
            return self._control

    def __init__(self, fields: list[DynamicField], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._initial_fields = fields

    def compose(self) -> ComposeResult:
        yield VerticalScroll()

    async def on_mount(self) -> None:
        self.fields_container: VerticalScroll = self.query_one(VerticalScroll)

        # Set initial_fields
        for field in self._initial_fields:
            await self.add_field(field=field)

    @property
    def fields(self) -> list[DynamicField]:
        return list(self.query(DynamicField))

    @property
    def empty_fields(self) -> list[DynamicField]:
        return [field for field in self.query(DynamicField) if field.is_empty]

    @property
    def filled_fields(self) -> list[DynamicField]:
        return [field for field in self.query(DynamicField) if field.is_filled]

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
            message=self.FieldEmpty(control=self, field=message.control)
        )

    @on(DynamicField.Filled)
    async def on_field_is_filled(self, message: DynamicField.Filled) -> None:
        if len(self.empty_fields) == 0:
            await self.add_field(
                field=DynamicField(enabled=False, key='', value='')
            )

        self.post_message(
            message=self.FieldFilled(control=self, field=message.control)
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
