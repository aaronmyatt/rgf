from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import Static, Footer, Input
from textual import events
from .base_screen import BaseScreen


class BlankScreen3(BaseScreen):
    id = "blank3"
    BINDINGS = BaseScreen.COMMON_BINDINGS + []
    
    def compose(self) -> ComposeResult:
        yield Static("Blank Screen 3 (press 1/2/3 to switch screens)", classes="header")
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        super().on_key(event)
