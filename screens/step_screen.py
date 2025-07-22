from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import Static, Footer, Input
from textual import events
from .base_screen import BaseScreen, FlowHeader
from app_actions import get_active_flow_id


class StepScreen(BaseScreen):
    id = "steps"
    BINDINGS = BaseScreen.COMMON_BINDINGS + []
    
    def compose(self) -> ComposeResult:
        yield FlowHeader()
        yield Static("Blank Screen 3 (press 1/2/3 to switch screens)", classes="header")
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        super().on_key(event)

    def on_mount(self):
        """checks for an active flow and returns the matches for it"""
        self.update_flow_name_in_header()

    async def on_screen_resume(self, event):
        await super().on_screen_resume(event)  # Update header
        
# ai? please plan how to update this file with a ListView that will present syntax highlighted FlowMatches from the database. You will need to update `app_actions` with a function to fetch flow matches from the db. Here's an example of how to use TextAreas:
# from textual.app import App, ComposeResult
# from textual.widgets import TextArea

# TEXT = """\
# def hello(name):
#     print("hello" + name)

# def goodbye(name):
#     print("goodbye" + name)
# """


# class TextAreaExample(App):
#     def compose(self) -> ComposeResult:
#         yield TextArea.code_editor(TEXT, language="python")


# app = TextAreaExample()
# if __name__ == "__main__":
#     app.run()