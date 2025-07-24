from textual.binding import Binding
from textual.widgets import Static
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


class FlowHeader(Static):
    """Header displaying the active flow name"""
    id="flow_header"
    
    DEFAULT_CSS = '''
    FlowHeader {
        background: dodgerblue;
        color: white;
        text-align: center;
        width: 100%;
        padding: 1;
    }
    '''
    
    def __init__(self):
        super().__init__("No active flow")
        self.styles.width = "100%"
        self.styles.text_align = "center"
        self.styles.background = "dodgerblue"
        self.styles.color = "white"
        self.styles.padding = (0, 1)


class BaseScreen(Screen):
    """Base screen with common navigation functionality."""

    COMMON_BINDINGS = [
        Binding(key="1", action="goto_search", description="Search", show=True),
        Binding(key="2", action="goto_flows", description="Flows", show=True),
        Binding(key="3", action="goto_steps", description="Steps", show=True),
        Binding(key="q", action="quit", description="Quit", show=True),
        # Add this new binding for quick search access
        Binding(key="/", action="goto_search", description="Search", show=True),
    ]

    def action_goto_search(self):
        """Action to navigate to search screen"""
        self.app.push_screen('search')

    def action_goto_flows(self):
        """Action to navigate to flows screen"""
        self.app.push_screen('flows')

    def action_goto_steps(self):
        """Action to navigate to steps screen"""
        self.app.push_screen('steps')

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
        header = self.query_one(FlowHeader)
        if event.flow_name == None:
            header.update("No active flow")
        else:
            header.update(event.flow_name) 
            
    async def on_screen_resume(self, event):
        """Update header with current active flow when screen becomes active"""
        self.update_flow_name_in_header()

    def update_flow_name_in_header(self):
        from app_actions import get_active_flow

        active_flow = get_active_flow(self.app.db, self.app.session_start)
        header = self.query_one(FlowHeader)

        if active_flow is None:
            header.update("No active flow")
        else:
            header.update(active_flow.name)
