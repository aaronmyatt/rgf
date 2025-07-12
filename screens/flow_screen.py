from textual.app import ComposeResult
from textual.widgets import Static, Footer, ListView, ListItem, Label
from textual import events
from .base_screen import BaseScreen
from db import Flow, list_rows
from app_actions import activate_flow

def flow_dom_id(flow):
    return 'wat'+str(hash(f"{flow.id}{flow.name}"))

class FlowScreen(BaseScreen):
    id = "flows"
    BINDINGS = BaseScreen.COMMON_BINDINGS + [
        ("a", "activate_selected_flow", "Activate Flow"),
        ("r", "refresh_flows", "Refresh"),
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
                    list_item = ListItem(Label(label_text))
                    list_item.id = flow_dom_id(flow)
                    flows_list.append(list_item)
                    
        except Exception as e:
            # Handle database errors gracefully
            flows_list = self.query_one("#flows_list", ListView)
            flows_list.clear()
            flows_list.append(ListItem(Label(f"Error loading flows: {str(e)}")))

    def on_list_view_highlighted(self, event):
        """Handle flow selection."""
        try:
            self.selected_flow = self.flows[event.list_view.index]
            print(f"WAT: highlighted: using index {self.selected_flow}")
        except IndexError:
            dom_id = event.item.id
            for flow in self.flows:
                if 'wat'+str(hash(f"{flow.id}{flow.name}")) == dom_id:
                    print(f"WAT: highlighted: using id {self.selected_flow}")
                    self.selected_flow = flow
                    break

    def on_list_view_selected(self, event):
        """Handle flow selection."""
        try:
            self.selected_flow = self.flows[event.list_view.index]
            print(f"WAT: on selected: using index {self.selected_flow}")
        except IndexError:
            dom_id = event.item.id
            for flow in self.flows:
                if 'wat'+str(hash(f"{flow.id}{flow.name}")) == dom_id:
                    print(f"WAT: on selected: using id {self.selected_flow}")
                    self.selected_flow = flow
                    break

    def action_refresh_flows(self):
        """Refresh the flows list."""
        self.run_worker(self.load_flows())

    def on_key(self, event):
        """Activate the currently selected flow."""
        print(f"WAT:activate {self.selected_flow}")
        if self.selected_flow and event.key == 'enter':
            try:
                activate_flow(self.app.db, self.selected_flow.id)
                self.notify(f"Activated flow: {self.selected_flow.name}")
            except Exception as e:
                self.notify(f"Error activating flow: {str(e)}", severity="error")

    def action_activate_selected_flow(self):
        """Activate the currently selected flow."""
        print(f"WAT:activate {self.selected_flow}")
        if self.selected_flow:
            try:
                activate_flow(self.app.db, self.selected_flow.id)
                self.notify(f"Activated flow: {self.selected_flow.name}")
            except Exception as e:
                self.notify(f"Error activating flow: {str(e)}", severity="error")