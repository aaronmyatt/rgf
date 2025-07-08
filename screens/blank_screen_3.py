from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import Static, Footer, Input
from textual import events
from textual.screen import Screen


class BlankScreen3(Screen):
    BINDINGS = [
        Binding(key="1", action="goto_screen_1", description="Screen 1", show=True),
        Binding(key="2", action="goto_screen_2", description="Screen 2", show=True),
        Binding(key="3", action="goto_screen_3", description="Screen 3", show=True),
        Binding(key="escape", action="unfocus_all", description="Unfocus", show=True),
        Binding(key="q", action="quit", description="Quit", show=True),
    ]
    
    def compose(self) -> ComposeResult:
        yield Static("Blank Screen 3 (press 1/2/3 to switch screens)", classes="header")
        yield Footer()

    def on_key(self, event: events.Key) -> None:
        if isinstance(self.focused, Input):
            if event.key in {"1", "2", "3"}:
                return
            if event.key == "escape":
                self.focused.blur()
                return
        if event.key == "1":
            self.action_goto_screen_1()
        elif event.key == "2":
            self.action_goto_screen_2()
        elif event.key == "3":
            self.action_goto_screen_3()
        elif event.key == "escape":
            self.action_unfocus_all()
        elif event.key == "q":
            self.app.exit()

    def action_goto_screen_1(self):
        self.app.push_screen(self.app.screen_search)

    def action_goto_screen_2(self):
        self.app.push_screen(self.app.screen_blank2)

    def action_goto_screen_3(self):
        self.app.push_screen(self.app.screen_blank3)

    def action_unfocus_all(self):
        if self.focused:
            self.focused.blur()
