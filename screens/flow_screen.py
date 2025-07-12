from textual.app import ComposeResult
from textual.widgets import Static, Footer, ListView, ListItem, Label
from textual import events
from .base_screen import BaseScreen
from db import Flow, list_rows
from app_actions import activate_flow


class FlowScreen(BaseScreen):
    id = "flows"
    BINDINGS = BaseScreen.COMMON_BINDINGS + [
        ("r", "refresh_flows", "Refresh"),
        ("enter", "activate_selected_flow", "Activate Flow"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flows = []
        self.selected_flow = None
    
    def compose(self) -> ComposeResult:
        yield Static("Flows", classes="header")
        yield ListView(id="flows_list")
        yield Footer()

    async def on_mount(self):
        """Load flows when screen is mounted."""
        await self.load_flows()

    async def load_flows(self):
        """Load all non-archived flows from database."""
        try:
            # Get all non-archived flows
            self.flows = list_rows(self.app.db, "flows", Flow, where="archived = ?", where_args=[False])
            
            # Update the ListView
            flows_list = self.query_one("#flows_list", ListView)
            flows_list.clear()
            
            if not self.flows:
                flows_list.append(ListItem(Label("No flows found. Create one from the search screen.")))
            else:
                for flow in self.flows:
                    # Show flow name and creation date
                    label_text = f"{flow.name}"
                    if flow.created_at:
                        label_text += f" (Created: {flow.created_at[:10]})"  # Just the date part
                    flows_list.append(ListItem(Label(label_text)))
                    
        except Exception as e:
            # Handle database errors gracefully
            flows_list = self.query_one("#flows_list", ListView)
            flows_list.clear()
            flows_list.append(ListItem(Label(f"Error loading flows: {str(e)}")))

    def on_list_view_selected(self, event):
        """Handle flow selection."""
        listview = self.query_one("#flows_list", ListView)
        self.selected_flow = self.flows[listview.index]

    def action_refresh_flows(self):
        """Refresh the flows list."""
        self.run_worker(self.load_flows())

    def action_activate_selected_flow(self):
        """Activate the currently selected flow."""
        if self.selected_flow:
            try:
                activate_flow(self.app.db, self.selected_flow.id)
                self.notify(f"Activated flow: {self.selected_flow.name}")
            except Exception as e:
                self.notify(f"Error activating flow: {str(e)}", severity="error")

    def on_key(self, event: events.Key) -> None:
        super().on_key(event)
