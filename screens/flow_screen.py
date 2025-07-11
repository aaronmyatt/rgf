from textual.app import ComposeResult
from textual.widgets import Static, Footer, ListView, ListItem, Label
from textual import events
from .base_screen import BaseScreen


class FlowScreen(BaseScreen):
    id = "flows"
    BINDINGS = BaseScreen.COMMON_BINDINGS + []
    
    def compose(self) -> ComposeResult:
        yield Static("Blank Screen 2 (press 1/2/3 to switch screens)", classes="header")
        yield ListView(
            ListItem(Label("One")),
            ListItem(Label("Two")),
            ListItem(Label("Three")),
        )
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        super().on_key(event)
