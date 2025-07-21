from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import Static, Footer, Input
from textual import events
from .base_screen import BaseScreen
from app_actions import get_active_flow_id


class StepScreen(BaseScreen):
    id = "steps"
    BINDINGS = BaseScreen.COMMON_BINDINGS + []
    
    def compose(self) -> ComposeResult:
        yield Static("Blank Screen 3 (press 1/2/3 to switch screens)", classes="header")
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        super().on_key(event)

    def on_mount(self):
        """checks for an active flow and returns the matches for it"""

        maybe_flow_id = get_active_flow_id(self.app.db)

    async def on_screen_resume(self, event):
        await super().on_screen_resume(event)  # Update header
        
