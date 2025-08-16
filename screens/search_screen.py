from os import system

from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import DataTable, TextArea, Input, Footer
from textual.widgets.data_table import CellDoesNotExist, RowDoesNotExist
from textual.containers import Horizontal, Vertical, Container
from textual import events
from rich.text import Text
from .base_screen import BaseScreen, FlowHeader, ActiveFlowChanged, FlowDataChanged

# Import shared logic from waystation.py
from waystation import Match, UserGrep, get_rg_matches, get_grep_ast_preview
from app_actions import activate_flow, delete_flow_match_for_match, get_active_flow_id, get_latest_flow, get_match, save_match, get_active_flow

def get_match_ids_for_flow(db, flow_id):
    """Return a set of match IDs for the given flow_id."""
    if not flow_id:
        return set()
    rows = db.execute(
        "SELECT matches_id FROM flow_matches WHERE flows_id = ?", (flow_id,)
    ).fetchall()
    return set(row[0] for row in rows)

def get_matches_for_flow(db, flow_id):
    """Return a set of match IDs for the given flow_id."""
    if not flow_id:
        return set()
    rows = db.query(
        "SELECT * FROM flow_matches fm, matches m WHERE flows_id = ? AND fm.matches_id = m.id", (flow_id,)
    )
    return rows

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
    BINDINGS = [
        Binding("escape", "unfocus_all", "Cancel", show=True),
        Binding("enter", "submit", "Submit", show=True, priority=True)
    ]

    def __init__(self, args=UserGrep("", []), **kwargs):
        super().__init__(**kwargs)
        self.user_grep = args

    def compose(self):
        with Horizontal():
            yield Input(placeholder="Pattern", id="pattern_input", classes="w-half", value=self.user_grep.pattern if self.user_grep else "")
            yield Input(placeholder="Path(s) (optional, space separated)", id="paths_input", classes="w-half", value=' '.join(self.user_grep.paths) if self.user_grep else "")

    def action_unfocus_all(self):
        self.set_focus(None)

class GrepAstPreview(TextArea):
    id="grep_ast_preview"

    def update_preview(self, match: Match):
        self.load_text(get_grep_ast_preview(match))

class SearchScreen(BaseScreen):
    CSS = '''
'''

    id = "search"
    BINDINGS = [
        Binding(key="/", action="new_search", description="New Search", show=True, priority=True),
        # Binding(key="s", action="save_match", description="Save Match", show=False),
        Binding(key="enter", action="save_match", description="Save Match", show=True, priority=True),
        Binding(key="d", action="delete_match", description="Remove match", show=True),
        Binding(key="shift+enter", action="open_in_editor", description="Open in editor", show=True),
        # Binding(key="j", action="cursor_down", show=False),
        # Binding(key="k", action="cursor_up", show=False),
        # Binding(key="ctrl+f", action="page_down", show=False),
        # Binding(key="ctrl+b", action="page_up", show=False),
        # Binding(key="ctrl+n", action="cursor_down", show=False),
        # Binding(key="ctrl+p", action="cursor_up", show=False),
        # Binding(key="ctrl+v", action="page_down", show=False),
        # Binding(key="meta+v", action="page_up", show=False),
    ]


    # TODO: better create SearchDataTable to override all these
    def action_cursor_up(self):
        self.dg.action_cursor_up()

    def action_cursor_down(self):
        self.dg.action_cursor_down()


    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Hide common bindings when inputs are focused"""
        if isinstance(self.focused, Input):
            return action in {"unfocus_all", "submit_input"}
        return True

    def __init__(self, user_grep: UserGrep = None):
        super().__init__()
        self.user_grep = user_grep or self.app.user_grep
        self.matches: list[Match] = []
        self.dg = None
        self.preview = None
        # This attribute will store the current filter string as the user types while the DataTable is focused.
        # It will be displayed above the DataTable, but will not affect filtering yet.
        self.table_filter = ""

    def compose(self) -> ComposeResult:
        # Compose the UI layout for the SearchScreen.
        yield FlowHeader()
        self.dg = DataTable(zebra_stripes=True, id="matches_table")
        self.dg.cursor_type = "row"
        self.dg.add_columns("File", "Line", "Text")
        self.preview = GrepAstPreview(read_only=True)
        with Vertical():
            # Add a Label above the DataTable to display the current filter string.
            # This will be updated as the user types while the DataTable is focused.
            from textual.widgets import Label
            yield Label("", id="table_filter_label", classes="filter-label")
            with Horizontal(classes="h-11div12"):
                yield self.dg
                with Vertical():
                    yield self.preview
            yield UserGrepInput(self.user_grep, classes="h-1div12")
        yield Footer()

    def on_mount(self):
        if self.user_grep:
            self.matches = get_rg_matches(self.user_grep)
            self.focus_datatable()
        else:
            self.focus_search_input()

        self.render_matches()

    def render_matches(self, initial_selection=0):
        """
        Render the DataTable rows, filtered by self.table_filter if set.
        Only matches containing the filter string in file name, line, or line number are shown.
        """
        self.dg.clear()
        filter_str = self.table_filter.lower().strip()

        # Sort matches as before: saved matches (in flow) appear first
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)
        saved_matches = list(get_matches_for_flow(self.app.db, flow_id))
        lines = [match.get('line') for match in saved_matches]
        file_paths = [match.get('file_path') for match in saved_matches]
        sorted_matches = sorted(self.matches, key=lambda m: 0 if m.line in lines and m.file_path in file_paths else 1)

        # Filter matches if filter_str is not empty
        if filter_str:
            # Filter matches: show only those where the filter string appears in file_name, line, or line_no
            filtered_matches = [
                m for m in sorted_matches
                if filter_str in m.file_name.lower()
                or filter_str in m.line.lower()
                or filter_str in str(m.line_no)
            ]
        else:
            filtered_matches = sorted_matches

        # Add filtered matches to the DataTable
        for match in filtered_matches:
            self.dg.add_row(
                Text(match.file_name),
                Text(str(match.line_no)),
                Text(match.line)
            )

        self.screen.post_message(FlowDataChanged())
        # If there are filtered matches, select the first row and update preview
        if filtered_matches:
            self.update_preview(0)
            self.dg.move_cursor(row=initial_selection)
        else:
            self.update_preview(0)

    def on_input_submitted(self, event):
        pattern = self.query_one("#pattern_input").value
        paths = self.query_one("#paths_input").value.split()
        self.user_grep = UserGrep(pattern, paths)
        self.on_mount()

    def update_preview(self, match):
        try:
            self.preview.update_preview(match)
        except Exception as e:
            self.preview.update_preview(Match("<no preview>", 0, str(e)))

    def on_data_table_row_highlighted(self, event):
        # if not event.row_key or not event.row_key.value: return
        try:
            row = self.dg.get_row(event.row_key)
            match = next((match for match in self.matches if match.file_name == row[0].plain and match.line_no == int(row[1].plain) and match.line == row[2].plain), None)
            self.update_preview(match)
        except (CellDoesNotExist, RowDoesNotExist):
            """likely an empty table"""

    async def on_key(self, event: events.Key) -> None:
        # Prevent screen switching if an Input is focused
        await super().on_key(event)

        # If the DataTable is focused (and not an Input), capture typed keys to build the filter string.
        # Now, also filter the DataTable as the filter string changes.
        if self.focused == self.dg:
            # Handle backspace: remove last character from filter string
            if event.key == "backspace":
                self.table_filter = self.table_filter[:-1]
            # Handle printable characters: add to filter string (including spacebar)
            elif event.key == "space":
                self.table_filter += " "
            elif len(event.key) == 1 and event.key.isprintable():
                self.table_filter += event.key
            # Handle escape: clear the filter string
            elif event.key == "escape":
                self.table_filter = ""
            # Update the label above the DataTable to show the current filter string
            self.update_table_filter_label()
            # Re-render the DataTable with the filtered results
            self.render_matches()
            # Do not return here; allow other key handling to proceed as normal

        if self.focused != self.dg and isinstance(self.focused, Input):
            if event.key in {"1", "2", "3"}:
                return
            if event.key == "escape":
                self.focused.blur()
                return
        elif event.key == "enter" and self.focused == self.dg:
            self.action_save_match()
        elif event.key == "escape":
            self.action_unfocus_all()

    def update_table_filter_label(self):
        """
        Update the label above the DataTable to show the current filter string.
        This provides immediate feedback to the user as they type.
        """
        from textual.widgets import Label
        # Query for the label widget by its id
        filter_label = self.query_one("#table_filter_label", Label)
        # Set the label text to show the filter string, or clear if empty
        if self.table_filter:
            filter_label.update(f"Filter: {self.table_filter}")
        else:
            filter_label.update("")
    
    def action_unfocus_all(self):
        self.set_focus(None)

    def on_data_table_row_selected(self, event):
        if not event.row_key: return
        try:
            row = self.dg.get_row(event.row_key)
            match = next((match for match in self.matches if match.file_name == row[0].plain and match.line_no == int(row[1].plain) and match.line == row[2].plain), None)
            self.update_preview(match)
        except CellDoesNotExist:
            """likely an empty table"""

    def action_open_in_editor(self):
        idx = self.dg.cursor_coordinate.row
        match = self.matches[idx]
        try:
            with self.app.suspend():
                system(f'$EDITOR {match.filename} +{match.line_no}')
        except Exception as e:
            self.app.exit(str(e))

    def action_save_match(self):
        """Save the currently selected match to the database."""
        if not self.matches:
            self.notify("No matches available.", severity="warning")
            return

        idx = self.dg.cursor_coordinate.row
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)     

        match = self.matches[idx]
        save_match(self.app.db, match, flow_id=flow_id)
        if flow_id:
            """do nothing"""
        else:
            flow = get_latest_flow(self.app.db)
            activate_flow(self.app.db, flow.id)
            
        # Get updated active flow name
        active_flow = get_active_flow(self.app.db, self.app.session_start)
        flow_name = active_flow.name if active_flow else "No active flow"
        self.post_message(ActiveFlowChanged(flow_name))

        self.notify(f"Match saved: {match.file_name} at line {match.line_no}")

        # TODO: we can be smarter about moving selected items to the top. This is rerendering the whole list 
        self.render_matches(initial_selection=idx)

        # Notify other screens that flow data has changed (e.g., match count)
        self.screen.post_message(FlowDataChanged())

    def action_new_search(self):
        """Focus on the pattern input and clear it for a new search."""
        pattern_input = self.query_one("#pattern_input", Input)
        # clear preview
        self.preview.load_text("<no preview>")
        pattern_input.value = ""
        pattern_input.focus()

    def on_active_flow_changed(self, event: ActiveFlowChanged):
        """Update row highlighting when the active flow changes."""
        self.update_flow_name_in_header()
        self.refresh_row_highlighting()

    async def on_screen_resume(self, event):
        await super().on_screen_resume(event)  # Update header
        self.refresh_row_highlighting()
        if len(self.matches) == 0:
            self.focus_search_input()

    def focus_search_input(self):
        self.query_one("#pattern_input").focus()

    def focus_datatable(self):
        self.query_one(DataTable).focus()

    def refresh_row_highlighting(self):
        """Update row highlighting based on which matches belong to the active flow."""
        if not hasattr(self, "dg") or not self.dg or not hasattr(self, "matches"):
            return
        
        # TODO: find a more sensible way to clear these previous match colours
        # probably stop when we find the first row that is not green?

        for row in self.dg.ordered_rows:
            for cell in self.dg.get_row(row.key):
                cell.style = 'white on black'

        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)
        saved_matches = list(get_matches_for_flow(self.app.db, flow_id))
        lines = [match.get('line', '').strip() for match in saved_matches]
        file_names = [match.get('file_name') for match in saved_matches]
        for row in self.dg.ordered_rows[:len(set([m.get('matches_id') for m in saved_matches]))]:
                real_row = self.dg.get_row(row.key)
                if(real_row[0].plain in file_names and real_row[2].plain.strip() in lines):
                    for cell in real_row:
                        cell.style = 'black on green'

    async def action_delete_match(self):
        """Delete currently selected match from active flow"""
        if not self.matches:
            self.notify("No matches available.", severity="warning")
            return

        idx = self.dg.cursor_coordinate.row
        match = self.matches[idx]
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)

        if not flow_id:
            self.notify("No active flow selected.", severity="warning")
            return

        # Get database match ID
        match = get_match(self.app.db, match)
        if not match:
            self.notify("Match not found in flow", severity="warning")
            return

        # Delete from flow
        if delete_flow_match_for_match(self.app.db, flow_id, match.id):
            self.notify("Match removed from flow")
            self.render_matches()
        else:
            self.notify("Match not found in flow", severity="warning")

    async def on_flow_data_changed(self, event):
        self.refresh_row_highlighting()