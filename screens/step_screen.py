from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import Footer, ListView, ListItem, TextArea, Label, Input, Button
from textual.containers import Container, Horizontal
from textual import events
from .base_screen import BaseScreen, FlowHeader
from app_actions import get_active_flow_id, get_flow_matches
from db import Match, FlowMatch
from waystation import get_plain_lines_from_file, get_language_from_filename


class MatchNoteOverlay(Container):
    """Overlay for adding match notes"""
    def __init__(self, match: Match):
        super().__init__()
        self.match = match
        self.title_input = Input(id="title_input")
        self.note_input = TextArea(id="note_input", language="markdown")
        
    def compose(self) -> ComposeResult:
        yield Label(f"Add Note: {self.match.file_name}:{self.match.line_no}")
        yield Label("Title:")
        yield self.title_input
        yield Label("Note:")
        yield self.note_input
        with Horizontal():
            yield Button("Save", variant="primary", id="save")
            yield Button("Cancel", variant="error", id="cancel")
        
    def on_mount(self):
        self.title_input.focus()
        
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel":
            self.remove()
        elif event.button.id == "save":
            from app_actions import add_match_note
            from db import MatchNote
            
            # Create and save match note
            new_note = MatchNote(
                match_id=self.match.id,
                name=self.title_input.value,
                note=self.note_input.text
            )
            add_match_note(self.app.db, new_note)
            self.remove()
            self.app.notify("Note saved successfully!")

class StepScreen(BaseScreen):
    CSS = """
    /* Add new styles */
    .step-header {
        margin-bottom: 1;
    }
    .step-number {
        color: $accent;
        font-weight: bold;
        margin-right: 0.5;
    }
    .note-indicator {
        color: $warning;
        margin-left: 1;
    }
    .note-container {
        background: $surface;
        border-top: 1px dashed $accent;
        padding: 1;
        margin-top: 1;
    }
    .note-title {
        font-weight: bold;
        color: $text;
        margin-bottom: 0.5;
    }
    .note-content {
        background: $surface-darken-1;
    }
    .flow-step {
        border-left: 3px solid $primary;
        padding-left: 1;
        margin: 1 0;
    }
    MatchNoteOverlay {
        background: $background;
        border: $primary;
        width: 80%;
        height: auto;
        padding: 1;
        layer: overlay;
    }
    MatchNoteOverlay Input,
    MatchNoteOverlay TextArea {
        width: 100%;
    }
    """
    id = "steps"
    BINDINGS = [
        Binding("shift+up", "move_up", "Move Up", show=True),
        Binding("shift+down", "move_down", "Move Down", show=True),
        Binding("e", "add_match_note", "Add Note", show=True),
        Binding("n", "toggle_notes", "Toggle Notes", show=True),  # New binding
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flow_matches = []
        self._selected_index = 0
        self.editing_flow = False
        self.show_notes = True  # Default to showing notes

    def action_toggle_notes(self):
        """Toggle note visibility globally"""
        self.show_notes = not self.show_notes
        if hasattr(self.app, "config"):
            self.app.config["show_notes"] = self.show_notes
        self.refresh_list_items()

    def refresh_list_items(self):
        """Refresh list items with current note visibility"""
        list_view = self.query_one("#matches_list")
        list_view.clear()
        
        for idx, (match, flow_match, note) in enumerate(self.flow_matches):
            list_view.append(
                self.create_match_list_item(
                    match, 
                    flow_match,
                    note,
                    selected=(idx == self._selected_index)
                )
            )
        
        if self.flow_matches:
            list_view.index = self._selected_index

    async def on_mount(self):
        self.update_flow_name_in_header()
        await self.load_flow_matches()
        self.query_one(ListView).focus()

    async def on_screen_resume(self, event):
        """Restore note visibility state when returning to screen"""
        await super().on_screen_resume(event)
        if hasattr(self.app, "config"):
            self.show_notes = self.app.config.get("show_notes", True)
        await self.load_flow_matches()

    async def load_flow_matches(self):
        """Load matches for the active flow"""
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)
        
        matches_list = self.query_one("#matches_list", ListView)
        await matches_list.clear()
        
        if not flow_id:
            matches_list.append(ListItem(Label("No active flow. Activate a flow from the Flows screen.")))
            return
            
        self.flow_matches = get_flow_matches(self.app.db, flow_id)
        self._selected_index = 0
        
        if self.flow_matches and all(fm.order_index == 0 for _, fm, _ in self.flow_matches):
            self.initialize_flow_match_order()
        
        if not self.flow_matches:
            matches_list.append(ListItem(Label("No matches in this flow.")))
            return
            
        for idx, (match, flow_match, note) in enumerate(self.flow_matches):
            matches_list.append(
                self.create_match_list_item(
                    match, 
                    flow_match,
                    note,
                    selected=(idx == self._selected_index)
                )
            )

    def create_match_list_item(
        self, 
        match: Match, 
        flow_match: FlowMatch, 
        note,
        selected: bool = False
    ) -> ListItem:
        """Create a ListItem with syntax-highlighted code and note"""
        # Step header with note indicator
        step_num = flow_match.order_index + 1
        header = Container(classes="step-header")
        header.mount(Label(f"Step ", classes="step-number"))
        header.mount(Label(f"{step_num}: {match.file_name}:{match.line_no}"))
        
        if note:
            header.mount(Label("📝", classes="note-indicator"))
        
        # Code area
        preview_text = get_plain_lines_from_file(match, 3)
        language = get_language_from_filename(match.file_name)
        code_area = TextArea.code_editor(
            preview_text, 
            language=language,
            read_only=True,
            show_line_numbers=True,
            classes="h-auto"
        )
        
        # Main container
        main_container = Container(classes="flow-step")
        main_container.mount(header)
        main_container.mount(code_area)
        
        # Note section (conditionally visible)
        if note and self.show_notes:
            note_container = Container(classes="note-container")
            note_container.mount(Label(note.name, classes="note-title"))
            note_container.mount(TextArea(
                note.note, 
                read_only=True, 
                classes="note-content"
            ))
            main_container.mount(note_container)
        
        return ListItem(main_container, classes="h-auto")

    # ---- Reordering functionality ----
    
    async def action_move_up(self):
        """Move current item up in the list"""
        if self._selected_index > 0:
            await self._swap_items(self._selected_index, self._selected_index - 1)
            await self._refresh_list_view()

    async def action_move_down(self):
        """Move current item down in the list"""
        if self._selected_index < len(self.flow_matches) - 1:
            await self._swap_items(self._selected_index, self._selected_index + 1)
            await self._refresh_list_view()

    async def _swap_items(self, index1: int, index2: int) -> None:
        """Swap two items in the list and database"""
        try:
            self.app.db.execute("BEGIN TRANSACTION")
            
            # Get items to swap
            _, flow_match1, _ = self.flow_matches[index1]
            _, flow_match2, _ = self.flow_matches[index2]
            
            # Swap order indices
            flow_match1.order_index, flow_match2.order_index = (
                flow_match2.order_index,
                flow_match1.order_index
            )
            
            # Update database
            self._update_flow_match_order(flow_match1)
            self._update_flow_match_order(flow_match2)
            
            # Update local ordering
            self.flow_matches[index1], self.flow_matches[index2] = (
                self.flow_matches[index2], self.flow_matches[index1]
            )
            
            # Update selection index
            self._selected_index = index2
            self.app.db.execute("COMMIT")
        except Exception as e:
            # update didn't workout, reload flow to ensure onscreen order is correct
            self.app.db.execute("ROLLBACK")
            self.notify(f"Failed to initialize order indices: {str(e)}", severity="error")
            self.load_flow_matches()

    def _update_flow_match_order(self, flow_match: FlowMatch) -> None:
        """Update a single flow_match's order in the database"""
        self.app.db.execute(
            "UPDATE flow_matches SET order_index = ? WHERE id = ?",
            [flow_match.order_index, flow_match.id]
        ).rowcount

    async def _refresh_list_view(self):
        """Refresh the list view while maintaining selection"""
        list_view = self.query_one("#matches_list")
        await list_view.clear()
        
        for idx, (match, flow_match, note) in enumerate(self.flow_matches):
            list_view.append(
                self.create_match_list_item(
                    match, 
                    flow_match,
                    note,
                    selected=(idx == self._selected_index)
                )
            )
        
        # Ensure selected item is visible
        if self.flow_matches:
            list_view.index = self._selected_index

    # ---- Selection navigation ----
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation"""
        super().on_key(event)
        if event.key == "up":
            self._navigate_selection(-1)
        elif event.key == "down":
            self._navigate_selection(1)
    
    def _navigate_selection(self, direction: int):
        """Move selection up or down"""
        if not self.flow_matches:
            return
            
        new_index = max(0, min(len(self.flow_matches) - 1, self._selected_index + direction))
        if new_index != self._selected_index:
            self._selected_index = new_index

    def action_add_match_note(self):
        """Show note overlay for the selected match"""
        if not self.flow_matches:
            return
            
        # Get the match from the selected flow_match
        match, _, _ = self.flow_matches[self._selected_index]
        overlay = MatchNoteOverlay(match)
        self.mount(overlay)
        overlay.title_input.focus()

    def initialize_flow_match_order(self):
        try:
            # Start transaction
            self.app.db.execute("BEGIN TRANSACTION")
            
            # Update each flow_match with sequential order_index
            for index, (_, flow_match, _) in enumerate(self.flow_matches):
                flow_match.order_index = index
                self._update_flow_match_order(flow_match)
            
            # Commit changes
            self.app.db.execute("COMMIT")
        except Exception as e:
            # Rollback on error
            self.app.db.execute("ROLLBACK")
            self.notify(f"Failed to initialize order indices: {str(e)}", severity="error")
        
