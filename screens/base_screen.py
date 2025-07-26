from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Header, Tab, Tabs
from textual import events
from textual.screen import Screen
from textual.message import Message

class ActiveFlowChanged(Message):
    """Posted when active flow changes"""
    def __init__(self, flow_name: str):
        self.flow_name = flow_name
        super().__init__()

class FlowDataChanged(Message):
    """Posted when flow data (such as match counts) changes."""
    pass


class FlowHeader(Widget):
    """Header displaying the active flow name"""
    id="flow_header"

    def compose(self):
        yield Header()
        yield Tabs(
            Tab('Search (1)', id='search'),
            Tab('Flows (2)', id='flows'),
            Tab('Steps (3)', id='steps'),
            active=self.app.screen.id
        )


class BaseScreen(Screen):
    """Base screen with common navigation functionality."""

    BINDINGS = [
        Binding(key="1", action="goto_search", description="Search", show=False),
        Binding(key="2", action="goto_flows", description="Flows", show=False),
        Binding(key="3", action="goto_steps", description="Steps", show=False),
        Binding(key="q", action="quit", description="Quit", show=True),
        # Add this new binding for quick search access
        Binding(key="/", action="goto_search", description="Search", show=True),
    ]

    async def action_goto_search(self):
        """Action to navigate to search screen"""
        await self.app.push_screen('search')
        tabs = self.query(Tab)
        tab = next(tab for tab in tabs if tab.id == 'search')
        self.query_one(Tabs)._activate_tab(tab)

    def action_goto_flows(self):
        """Action to navigate to flows screen"""
        self.app.push_screen('flows')
        tabs = self.query(Tab)
        tab = next(tab for tab in tabs if tab.id == 'flows')
        self.query_one(Tabs)._activate_tab(tab)

    def action_goto_steps(self):
        """Action to navigate to steps screen"""
        self.app.push_screen('steps')
        tabs = self.query(Tab)
        tab = next(tab for tab in tabs if tab.id == 'steps')
        self.query_one(Tabs)._activate_tab(tab)

    def on_tab_activated(self, event):
        print(event)

    def on_key(self, event: events.Key) -> None:
        """Common key handling with Input focus prevention."""       
        if event.key == "1":
            self.action_goto_search()
        elif event.key == "2":
            self.action_goto_flows()
        elif event.key == "3":
            self.action_goto_steps()
        elif event.key == "q":
            self.app.exit()
        
    def on_active_flow_changed(self, event: ActiveFlowChanged):
        """Update header text when active flow changes"""
        if event.flow_name == None:
            self.title = "No active flow"
        else:
            self.title = event.flow_name
            
    async def on_screen_resume(self, event):
        """Update header with current active flow when screen becomes active"""
        self.update_flow_name_in_header()

    def update_flow_name_in_header(self):
        from app_actions import get_active_flow

        active_flow = get_active_flow(self.app.db, self.app.session_start)

        if active_flow is None:
            self.title = "No active flow"
        else:
            self.title = active_flow.name
