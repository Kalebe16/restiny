from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Select

if TYPE_CHECKING:
    from restiny.ui.app import RESTinyApp


class TopBarArea(Widget):
    app: 'RESTinyApp'

    DEFAULT_CSS = """
    TopBarArea {
        width: 1fr;
        height: auto;
        align: right middle;
    }

    Select {
        width: 24;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes='w-auto h-auto'):
            yield Select(
                [],
                prompt='No environment',
                allow_blank=True,
                compact=True,
                id='environment',
            )

    def on_mount(self) -> None:
        self.environment_select = self.query_one('#environment', Select)

        self.populate()

    @property
    def environment(self) -> str:
        if self.environment_select.value == Select.BLANK:
            return None

        return self.environment_select.value

    def populate(self) -> None:
        prev_selected_environment = self.environment_select.value
        environments = [
            environment.name
            for environment in self.app.environments_repo.get_all().data
            if environment.name != 'global'
        ]
        self.environment_select.set_options(
            (environment, environment) for environment in environments
        )
        if prev_selected_environment in environments:
            self.environment_select.value = prev_selected_environment
