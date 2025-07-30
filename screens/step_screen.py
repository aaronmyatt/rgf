from typing import Optional, Tuple
from textual.binding import Binding
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Footer, ListView, ListItem, TextArea, Label, Input, Button, MarkdownViewer, Markdown
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from .base_screen import BaseScreen, FlowHeader
from app_actions import get_active_flow_id, get_flow_matches, update_match_note
from db import Match, FlowMatch, MatchNote
from waystation import get_plain_lines_from_file, get_language_from_filename

class NewMatchNote(Message):
    """"""
    def __init__(self, note: MatchNote):
        super().__init__()
        self.note = note

class MatchNoteOverlay(Container):
    """Overlay for adding match notes"""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, flow_match_extended: Tuple[Match, FlowMatch, Optional[MatchNote]]):
        super().__init__()
        self.match, self.flow_match, self.note = flow_match_extended
        self.title_input = Input(id="title_input")
        self.title_input.value = self.note.name if self.note else ""
        self.note_input = TextArea(id="note_input", language="markdown")
        self.note_input.text = self.note.note if self.note else ""
        
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

    def on_unmount(self):
        self.title_input.value = ""
        self.note_input.text = ""
        self.note = None
        
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel":
            self.remove()
        elif event.button.id == "save":
            from app_actions import add_match_note
            
            # Create and save match note
            new_note = MatchNote(
                flow_match_id=self.flow_match.id,
                name=self.title_input.value,
                note=self.note_input.text
            )
            if self.note:
                new_note.id = self.note.id
                update_match_note(self.app.db, new_note)
            else:
                add_match_note(self.app.db, new_note)
            self.app.notify("Note saved successfully!")
            self.post_message(NewMatchNote(new_note))
            self.remove()

    def action_cancel(self):
        """Handle cancel action"""
        self.remove()            

class EditFlowScreen(Screen):
    id = "edit steps"
    BINDINGS = [
        Binding("shift+up", "move_up", "Move Up", show=True),
        Binding("shift+down", "move_down", "Move Down", show=True),
        Binding("e", "add_match_note", "Add Note", show=True),
        Binding("enter", "add_match_note", "Add Note", show=False),
        Binding("q", "quit", "Close", show=True),
        Binding("escape", "quit", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield ListView(id="matches_list")
        yield Footer()

    async def on_mount(self):
        """Initialize the screen and load flow matches"""
        list_view = self.query_one(ListView)
        list_view.focus()
        await self.load_flow_matches()
        list_view.border_title = "Edit Flow"
        list_view.border_subtitle = f"Steps {len(self.flow_matches)}"

    async def load_flow_matches(self):
        """Load matches for the active flow"""
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)
        
        matches_list = self.query_one(ListView)
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
            
        for match, flow_match, note in self.flow_matches:
            matches_list.append(
                self.create_match_list_item(
                    match, 
                    flow_match,
                    note
                )
            )

    def create_match_list_item(
        self, 
        match: Match, 
        flow_match: FlowMatch, 
        note
    ) -> ListItem:
        """Create a ListItem with syntax-highlighted code and note"""
        # Step header with note indicator
        step_num = flow_match.order_index + 1
        children = [
            Label(f"Step ", classes="step-number"),
            Label(f"{step_num}: {match.file_name}:{match.line_no}")
        ]
        
        if note:
            children.append(Label("📝", classes="note-indicator"))
        
        header = Horizontal(*children, classes="step-header")
        
        # Main container
        main_container_children = [header]
                
        # Note section (conditionally visible)
        if note:
            note_container_children = []
            note_container_children.append(Label(note.name, classes="note-title")) if note.name else None
            note_container_children.append(
                TextArea(
                    note.note, 
                    language="markdown", 
                    read_only=True, 
                    classes="note-content"
                )
            ) if note.note else None
            note_container = Vertical(*note_container_children, classes="note-container")
            main_container_children.append(note_container)


        # Code area
        preview_text = get_plain_lines_from_file(match, 3)
        language = get_language_from_filename(match.file_name)
        code_area = TextArea.code_editor(
            preview_text, 
            language=language,
            read_only=True,
            show_line_numbers=True,
            classes="h-auto code-area"
        )

        main_container_children.append(code_area)
        main_container = Vertical(*main_container_children, classes="flow-step")
        return ListItem(main_container, classes="h-auto", id=f"order-{flow_match.order_index}")

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
        list_view = self.query_one(ListView)
        await list_view.clear()
        
        for idx, (match, flow_match, note) in enumerate(self.flow_matches):
            list_view.append(
                self.create_match_list_item(
                    match, 
                    flow_match,
                    note
                )
            )
        
        # Ensure selected item is visible
        if self.flow_matches:
            list_view.index = self._selected_index

    def on_list_view_selected(self, event):
        self._selected_index = int(event.item.id.split('-')[1])

    def on_list_view_highlighted(self, event):
        if event.item:
            self._selected_index = int(event.item.id.split('-')[1])

    async def on_new_match_note(self, event):
        await self.load_flow_matches()

    def action_add_match_note(self):
        """Show note overlay for the selected match"""
        if not self.flow_matches:
            return
            
        # Get the match from the selected flow_match
        flow_match_extended = self.flow_matches[self._selected_index]
        overlay = MatchNoteOverlay(flow_match_extended=flow_match_extended)
        self.mount(overlay)

    async def action_quit(self):
        """Close the EditFlowScreen"""
        await self.dismiss(self.flow_matches)

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
      
class StepScreen(BaseScreen):
    id = "steps"
    BINDINGS = [
        Binding("e", "edit_flow", "Edit Flow", show=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flow_matches = []
        self._selected_index = 0
        self.editing_flow = False
        self.show_notes = True  # Default to showing notes

    def compose(self) -> ComposeResult:
        yield FlowHeader()
        yield MarkdownViewer()
        yield Footer()

    def on_mount(self):
        # self.query_one(ListView).focus()
        self.update_flow_name_in_header()
        self.load_flow_matches()

    def on_screen_resume(self, event):
        """Restore note visibility state when returning to screen"""
        super().on_screen_resume(event)
        if hasattr(self.app, "config"):
            self.show_notes = self.app.config.get("show_notes", True)

    def load_flow_matches(self, flow_matches=None):
        """in markdown"""
        from waystation import flow_matches_to_markdown
        
        flow_id = get_active_flow_id(self.app.db, session_start=self.app.session_start)
        self.flow_matches = flow_matches or get_flow_matches(self.app.db, flow_id)
        md = flow_matches_to_markdown(self.flow_matches)
        self.query_one(Markdown).update(md)

    async def action_edit_flow(self):
        """Switch to EditFlowScreen"""
        def reload_flow_matches(flows):
            self.load_flow_matches(flows)

        await self.app.push_screen(EditFlowScreen(), reload_flow_matches)