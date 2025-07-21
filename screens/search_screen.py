from os import system

from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Input, Footer
from textual.widgets.data_table import CellDoesNotExist
from textual.containers import Horizontal, Vertical, Container
from textual import events
from rich.text import Text
from rich.style import Style
from .base_screen import BaseScreen, FlowHeader, ActiveFlowChanged, FlowDataChanged

# Import shared logic from waystation.py
from waystation import Match, UserGrep, get_rg_matches, get_grep_ast_preview
from app_actions import activate_flow, get_active_flow_id, get_latest_flow, save_match, get_active_flow

def get_match_ids_for_flow(db, flow_id):
    """Return a set of match IDs for the given flow_id."""
    if not flow_id:
        return set()
    rows = db.execute(
        "SELECT matches_id FROM flow_matches WHERE flows_id = ?", (flow_id,)
    ).fetchall()
    return set(row[0] for row in rows)

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
    id="grep_ast_preview"

    def update_preview(self, match: Match):
        self.update(get_grep_ast_preview(match))

class SearchScreen(BaseScreen):
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
.bg-green {
    background: #48bb78;
}
'''

    id = "search"
    title = "Ripgrep > grep-ast Browser"
    BINDINGS = BaseScreen.COMMON_BINDINGS + [
        Binding(key="n", action="new_search", description="New Search", show=True),
        Binding(key="s", action="save_match", description="Save Match", show=False),
        Binding(key="enter", action="save_match", description="Save Match", show=True),
        Binding(key="shift+enter", action="open_in_editor", description="Open in editor", show=True),
        Binding(key="escape", action="unfocus_all", description="Unfocus", show=True),
        Binding(key="up", action="cursor_up", description="Cursor Up", show=False),
        Binding(key="down", action="cursor_down", description="Cursor Down", show=False),
    ]

    def __init__(self, user_grep: UserGrep = None):
        super().__init__()
        self.user_grep = user_grep or self.app.user_grep
        self.matches: list[Match] = []
        self.dg = None
        self.preview = None

    def compose(self) -> ComposeResult:
        yield FlowHeader()
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
                self.dg.add_row(Text(match.file_name), Text(str(match.line_no)), Text(match.line), key=idx)
            self.dg.focus()
            self.dg.cursor_coordinate = 0, 0
            self.update_preview(0)
        else:  # No matches found
            self.update_preview(0)
        await self.refresh_row_highlighting()

    async def on_input_submitted(self, event):
        self.dg.clear()
        pattern = self.query_one("#pattern_input").value
        paths = self.query_one("#paths_input").value.split()
        self.user_grep = UserGrep(pattern, paths)
        await self.on_mount()
        await self.refresh_row_highlighting()

    def update_preview(self, idx):
        try:
            match = self.matches[idx]
            self.preview.update_preview(match)
        except Exception as e:
            self.preview.update_preview(Match("<no preview>", 0, str(e)))

    def action_cursor_up(self):
        cursor_coordinate = self.dg.cursor_coordinate
        try:
            cell_key = self.dg.coordinate_to_cell_key(cursor_coordinate)
            row_key, _ = cell_key
            self.update_preview(row_key.value - 1)
        except CellDoesNotExist:
            """likely an empty table"""

    def action_cursor_down(self):
        cursor_coordinate = self.dg.cursor_coordinate
        try:
            cell_key = self.dg.coordinate_to_cell_key(cursor_coordinate)
            row_key, _ = cell_key
            self.update_preview(row_key.value + 1)
        except CellDoesNotExist:
            """likely an empty table"""

    def on_key(self, event: events.Key) -> None:
        # Prevent screen switching if an Input is focused
        super().on_key(event)
        if isinstance(self.focused, Input):
            if event.key in {"1", "2", "3"}:
                return
            if event.key == "escape":
                self.focused.blur()
                return
        elif event.key == "enter" and self.focused == self.dg:
            self.action_save_match()
        elif event.key == "up":
            self.action_cursor_up()
        elif event.key == "down":
            self.action_cursor_down()
        elif event.key == "escape":
            self.action_unfocus_all()
    
    def action_unfocus_all(self):
        self.set_focus(None)

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

    async def action_save_match(self):
        """Save the currently selected match to the database."""
        if not self.matches:
            self.notify("No matches available.", severity="warning")
            return

        idx = self.dg.cursor_coordinate.row
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)     
        save_match(self.app.db, self.matches[idx], flow_id=flow_id)
        if flow_id:
            """do nothing"""
        else:
            flow = get_latest_flow(self.app.db)
            activate_flow(self.app.db, flow.id)
            
        # Get updated active flow name
        active_flow = get_active_flow(self.app.db, self.app.session_start)
        flow_name = active_flow.name if active_flow else "No active flow"
        self.post_message(ActiveFlowChanged(flow_name))
        
        self.notify(f"Match saved: {self.matches[idx].file_name} at line {self.matches[idx].line_no}")

        await self.refresh_row_highlighting()

        # Notify other screens that flow data has changed (e.g., match count)
        self.post_message(FlowDataChanged())

    def action_new_search(self):
        """Focus on the pattern input and clear it for a new search."""
        pattern_input = self.query_one("#pattern_input", Input)
        # clear preview
        self.preview.update("<no preview>")
        pattern_input.value = ""
        self.matches = []
        self.dg.clear()
        pattern_input.focus()

    async def on_active_flow_changed(self, event: ActiveFlowChanged):
        """Update row highlighting when the active flow changes."""
        await self.refresh_row_highlighting()

    async def on_screen_resume(self, event):
        """Update row highlighting when the active flow changes."""
        await self.refresh_row_highlighting()

    async def refresh_row_highlighting(self):
        """Update row highlighting based on which matches belong to the active flow."""
        if not hasattr(self, "dg") or not self.dg or not hasattr(self, "matches"):
            return
        # Clear all row highlighting
        for idx, match in enumerate(self.matches):
            row = self.dg.ordered_rows[idx] if idx < len(self.dg.ordered_rows) else None
            if row:
                for cell in self.dg.get_row(row.key):
                    cell.stylize(Style(bgcolor="black", color="white"))
        # Highlight rows for matches in the active flow
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)
        match_ids = get_match_ids_for_flow(self.app.db, flow_id)
        # We need to know the match id for each match in self.matches
        # Assume that Match has a .id attribute if it was saved, otherwise None
        # We'll try to look up the match id in the DB by file_path, line, etc if not present
        for idx, match in enumerate(self.matches):
            # Try to get match id from DB if not present
            match_id = getattr(match, "id", None)
            if match_id is None:
                # Try to look up by file_path, line, etc
                row = self.app.db.execute(
                    "SELECT id FROM matches WHERE file_path = ? AND line_no = ? AND line = ?",
                    (getattr(match, "file_path", getattr(match, "filename", "")), getattr(match, "line_no", 0), match.line)
                ).fetchone()
                if row:
                    match_id = row[0]
                    match.id = match_id
            if match_id in match_ids:
                row = self.dg.ordered_rows[idx] if idx < len(self.dg.ordered_rows) else None
                if row:
                    for cell in self.dg.get_row(row.key):
                        cell.stylize(Style(bgcolor="green", color="black"))
