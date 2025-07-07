from os import system

from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Static, Input, Footer, ListView, ListItem, Label

from textual.containers import Horizontal, Vertical, Container
from textual import events
from textual.content import Content
from textual.screen import Screen

# Import shared logic from waystation.py
from waystation import Match, UserGrep, get_rg_matches, get_grep_ast_preview

class UserGrepInput(Container):
    """
    Custom Input widget for UserGrep pattern input.
    It will submit the input when Enter is pressed.
    """
    DEFAULT_CSS = '''
.w-half {
    width: 50%;
}
'''
    def __init__(self, args=UserGrep("", []), **kwargs):
        super().__init__(**kwargs)
        self.user_grep = args

    def compose(self):
        with Horizontal():
            yield Input(placeholder="Pattern", id="pattern_input", classes="w-half", value=self.user_grep.pattern if self.user_grep else "")
            yield Input(placeholder="Path(s) (optional, space separated)", id="paths_input", classes="w-half", value=' '.join(self.user_grep.paths) if self.user_grep else "")

class GrepAstPreview(Static):
    def update_preview(self, match: Match):
        self.update(get_grep_ast_preview(match))

class SearchScreen(Screen):
    CSS = '''
.h-full {
    height: 100%;
}
.h-11div12 {
    height: 91.666667%;
}
.h-1div12 {
    height: 8.333333%;
}
.h-half {
    height: 50%;
}
.h-auto {
    height: auto;
}
'''

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit", show=True),
        Binding(key="up", action="cursor_up", description="Cursor Up", show=True),
        Binding(key="down", action="cursor_down", description="Cursor Down", show=True),
        Binding(key="enter", action="open_in_editor", description="Open in editor", show=True),
        Binding(key="n", action="new_search", description="New Search", show=True),
        Binding(key="1", action="goto_screen_1", description="Screen 1", show=True),
        Binding(key="2", action="goto_screen_2", description="Screen 2", show=True),
        Binding(key="3", action="goto_screen_3", description="Screen 3", show=True),
        Binding(key="escape", action="unfocus_all", description="Unfocus", show=True),
    ]

    def __init__(self, user_grep: UserGrep = None):
        super().__init__()
        self.user_grep = user_grep
        self.matches: list[Match] = []
        self.dg = None
        self.preview = None

    def compose(self) -> ComposeResult:
        self.dg = DataTable(zebra_stripes=True, id="matches_table")
        self.dg.cursor_type = "row"
        self.dg.add_columns("File", "Line", "Text")
        self.preview = GrepAstPreview(markup=False)
        with Vertical():
            with Horizontal(classes="h-11div12"):
                yield self.dg
                with Vertical():
                    yield Static("Ripgrep AST Browser", classes="header")
                    yield self.preview
            yield UserGrepInput(self.user_grep, classes="h-1div12")
        yield Footer()

    async def on_mount(self):
        if self.user_grep:
            self.matches = get_rg_matches(self.user_grep)
        else:
            self.query_one("#pattern_input").focus()

        if self.matches:
            for idx, match in enumerate(self.matches):
                self.dg.add_row(match.filename, str(match.line_no), Content(match.content), key=idx)
            self.dg.focus()
            self.dg.cursor_coordinate = 0, 0
            self.update_preview(0)

    async def on_input_submitted(self, event):
        pattern = self.query_one("#pattern_input").value
        paths = self.query_one("#paths_input").value.split()
        self.user_grep = UserGrep(pattern, paths)
        await self.on_mount()

    def update_preview(self, idx):
        try:
            match = self.matches[idx]
            self.preview.update_preview(match)
        except Exception as e:
            self.preview.update(str(e))

    def action_cursor_up(self):
        idx = self.dg.cursor_coordinate.row
        self.update_preview(idx-1)

    def action_cursor_down(self):
        idx = self.dg.cursor_coordinate.row
        self.update_preview(idx-1)

    def on_key(self, event: events.Key) -> None:
        # Prevent screen switching if an Input is focused
        if isinstance(self.focused, Input):
            if event.key in {"1", "2", "3"}:
                return
            if event.key == "escape":
                self.focused.blur()
                return
        if event.key == "q":
            self.app.exit()
        elif event.key == "enter" and self.focused == self.dg:
            self.action_open_in_editor()
        elif event.key == "up":
            self.action_cursor_up()
        elif event.key == "down":
            self.action_cursor_down()
        elif event.key == "escape":
            self.action_unfocus_all()
        elif event.key == "1":
            self.action_goto_screen_1()
        elif event.key == "2":
            self.action_goto_screen_2()
        elif event.key == "3":
            self.action_goto_screen_3()

    def on_data_table_row_selected(self, event):
        self.update_preview(event.row_key.value)

    def action_open_in_editor(self):
        idx = self.dg.cursor_coordinate.row
        match = self.matches[idx]
        try:
            with self.app.suspend():
                system(f'$EDITOR {match.filename} +{match.line_no}')
        except Exception as e:
            self.app.exit(str(e))

    def action_new_search(self):
        """Focus on the pattern input and clear it for a new search."""
        pattern_input = self.query_one("#pattern_input", Input)
        # clear preview
        self.preview.update("<no preview>")
        pattern_input.value = ""
        self.matches = []
        self.dg.clear()
        pattern_input.focus()

    def action_goto_screen_1(self):
        self.app.push_screen(self.app.screen_search)

    def action_goto_screen_2(self):
        self.app.push_screen(self.app.screen_blank2)

    def action_goto_screen_3(self):
        self.app.push_screen(self.app.screen_blank3)

    def action_unfocus_all(self):
        if self.focused:
            self.focused.blur()

class BlankScreen2(Screen):
    BINDINGS = [
        Binding(key="1", action="goto_screen_1", description="Screen 1", show=True),
        Binding(key="2", action="goto_screen_2", description="Screen 2", show=True),
        Binding(key="3", action="goto_screen_3", description="Screen 3", show=True),
        Binding(key="escape", action="unfocus_all", description="Unfocus", show=True),
        Binding(key="q", action="quit", description="Quit", show=True),
    ]
    def compose(self) -> ComposeResult:
        yield Static("Blank Screen 2 (press 1/2/3 to switch screens)", classes="header")
        yield ListView(
            ListItem(Label("One")),
            ListItem(Label("Two")),
            ListItem(Label("Three")),
        )
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

class RGApp(App):
    CSS_PATH = 'styles.tcss'

    def __init__(self, args: UserGrep = None):
        super().__init__()
        self.user_grep = args

    def on_mount(self):
        # Register screens
        self.screen_search = SearchScreen(self.user_grep)
        self.screen_blank2 = BlankScreen2()
        self.screen_blank3 = BlankScreen3()
        self.install_screen(self.screen_search, name="search")
        self.install_screen(self.screen_blank2, name="blank2")
        self.install_screen(self.screen_blank3, name="blank3")
        self.push_screen(self.screen_search)

if __name__ == "__main__":
    from waystation import init_waystation
    import argparse

    # Initialize the database and $HOME/.waystation directory
    init_waystation()

    parser = argparse.ArgumentParser(description="Textual ripgrep-ast browser")
    parser.add_argument('pattern', nargs='?', help="Pattern to search")
    parser.add_argument('paths', nargs='*', help="Search in these files/dirs")
    args = parser.parse_args()

    if args.pattern is None:
        RGApp().run()
    else:
        RGApp(UserGrep(args.pattern, args.paths)).run()
