from enum import StrEnum
from textual.app import ComposeResult
from textual.widgets import Static, Footer, ListView, ListItem, Label
from textual import events
from textual.containers import Container, Horizontal
from textual.widgets import Input, TextArea, Button
from .base_screen import BaseScreen, FlowHeader, ActiveFlowChanged
from db import Flow, list_rows, update_row
from app_actions import activate_flow, get_flow_match_counts

class Words(StrEnum):
    """Text constants for the FlowScreen."""
    HEADER = "Flows"
    NO_FLOWS_MESSAGE = "No flows found. Create one from the search screen."

class FlowEditOverlay(Container):
    """Overlay for editing flow details"""
    id = "flow_edit_overlay"
    
    def __init__(self, flow: Flow):
        super().__init__()
        self.flow = flow
        
    def compose(self) -> ComposeResult:
        yield Input(
            id="flow_name_input",
            value=self.flow.name,
            placeholder="Flow Name"
        )
        yield TextArea(
            id="flow_description_input",
            text=self.flow.description or "",
            classes="description-textarea"
        )
        with Horizontal():
            yield Button("Save", id="save_flow_button", variant="primary")
            yield Button("Cancel", id="cancel_flow_button")

    def on_mount(self):
        self.query_one("#flow_name_input").focus()

def flow_dom_id(flow):
    return 'wat'+str(hash(f"{flow.id}{flow.name}"))

class FlowScreen(BaseScreen):
    id = "flows"
    BINDINGS = BaseScreen.COMMON_BINDINGS + [
        ("a", "activate_selected_flow", "Activate Flow"),
        ("r", "refresh_flows", "Refresh"),
        ("e", "edit_flow", "Edit Flow"),
        ("n", "new_flow", "New Flow"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flows = []
        self.selected_flow = None
    
    def compose(self) -> ComposeResult:
        yield FlowHeader()
        yield Static(Words.HEADER, classes="header")
        yield ListView(id="flows_list")
        yield Footer()

    async def on_mount(self):
        """Load flows when screen is mounted."""
        self.update_flow_name_in_header()
        await self.load_flows()

    async def on_screen_resume(self, event):
        await super().on_screen_resume(event)  # Update header
        await self.load_flows()

    async def load_flows(self):
        """Load all non-archived flows from database."""
        try:
            # Get all non-archived flows
            self.flows = list_rows(self.app.db, "flows", Flow, where="archived = ?", where_args=[0])

            # Get match counts for all flows in a single query
            flow_ids = [flow.id for flow in self.flows]
            match_counts = {}
            if flow_ids:
                # Execute a single query to get counts for all flows
                results = get_flow_match_counts(self.app.db, flow_ids)
                match_counts = {row['flows_id']: row['match_count'] for row in results}

            # Update the ListView
            flows_list = self.query_one("#flows_list", ListView)
            await flows_list.clear()

            if not self.flows:
                flows_list.append(ListItem(Label(Words.NO_FLOWS_MESSAGE)))
            else:
                for flow in self.flows:
                    count = match_counts.get(flow.id)
                    count_text = f"{count} match{'es' if count != 1 else ''}"

                    # Show flow name, match count, and creation date
                    label_text = f"{flow.name} ({count_text})"
                    if flow.created_at:
                        label_text += f" [Created: {flow.created_at[:10]}]"  # Just the date part
                    list_item = ListItem(Label(label_text))
                    list_item.id = flow_dom_id(flow)
                    list_item.add_class('flow_list_item')
                    flows_list.append(list_item)

        except Exception as e:
            # Handle database errors gracefully
            flows_list = self.query_one("#flows_list", ListView)
            flows_list.clear()
            flows_list.append(ListItem(Label(f"Error loading flows: {str(e)}")))

    def on_list_view_highlighted(self, event):
        """Handle flow selection."""
        index = event.list_view.index
        if index is None: 
            return

        if 0 <= index < len(self.flows):
            self.selected_flow = self.flows[index]
        else:
            self.selected_flow = None

    def on_list_view_selected(self, event):
        """Handle flow selection."""
        index = event.list_view.index
        if index is None: 
            return
        
        if 0 <= index < len(self.flows):
            self.selected_flow = self.flows[index]
        else:
            self.selected_flow = None

    def action_refresh_flows(self):
        """Refresh the flows list."""
        self.run_worker(self.load_flows)

    async def on_flow_data_changed(self, event):
        """Refresh flows when notified that flow data has changed."""
        await self.load_flows()

    def on_key(self, event):
        """Activate the currently selected flow."""
        if self.selected_flow and event.key == 'enter':
            try:
                activate_flow(self.app.db, self.selected_flow.id)
                self.post_message(ActiveFlowChanged(self.selected_flow.name))
                self.notify(f"Activated flow: {self.selected_flow.name}")
            except Exception as e:
                self.notify(f"Error activating flow: {str(e)}", severity="error")

    def action_activate_selected_flow(self):
        """Activate the currently selected flow."""
        if self.selected_flow:
            try:
                activate_flow(self.app.db, self.selected_flow.id)
                self.post_message(ActiveFlowChanged(self.selected_flow.name))
                self.notify(f"Activated flow: {self.selected_flow.name}")
            except Exception as e:
                self.notify(f"Error activating flow: {str(e)}", severity="error")

    def action_edit_flow(self):
        """Show edit overlay for selected flow"""
        if self.selected_flow:
            # Create and mount new overlay
            overlay = FlowEditOverlay(self.selected_flow)
            self.mount(overlay)
            overlay.scroll_visible()

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses in the overlay"""
        if event.button.id == "save_flow_button":
            await self.save_flow_changes()
        elif event.button.id == "cancel_flow_button":
            overlay = self.query_one("#flow_edit_overlay")
            overlay.remove()

    def action_new_flow(self):
        """Create a new flow."""
        self.selected_flow = None
        new_flow = Flow(name="", description="")
        overlay = FlowEditOverlay(new_flow)
        self.mount(overlay)
        overlay.scroll_visible()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle Enter key in input fields."""
        if event.input.id == "flow_name_input":
            self.run_worker(self.save_flow_changes())

    async def save_flow_changes(self):
        """Save changes made in the edit overlay"""
        overlay = self.query_one("#flow_edit_overlay")
        name_input = overlay.query_one("#flow_name_input", Input)
        desc_input = overlay.query_one("#flow_description_input", TextArea)
        
        new_name = name_input.value.strip()
        new_desc = desc_input.text.strip()
        
        if not new_name:
            self.notify("Flow name cannot be empty", severity="error")
            return
        
        try:
            # Update flow in database
            if self.selected_flow and getattr(self.selected_flow, "id", None):
                # Existing flow update
                self.selected_flow.name = new_name
                self.selected_flow.description = new_desc or None
                update_row(self.app.db, "flows", self.selected_flow.id, self.selected_flow)
                action = "Updated"
            else:
                # New flow creation
                from app_actions import new_flow
                flow_id = new_flow(self.app.db, Flow(name=new_name, description=new_desc))
                action = "Created"
            
            # Refresh UI and close overlay
            self.notify(f"{action} flow: {new_name}")
            overlay.remove()
            await self.load_flows()
        except Exception as e:
            self.notify(f"Error saving flow: {str(e)}", severity="error")
