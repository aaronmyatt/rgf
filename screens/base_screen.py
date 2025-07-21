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
        Binding(key="1", action="goto_screen_1", description="Search", show=True),
        Binding(key="2", action="goto_screen_2", description="Flows", show=True),
        Binding(key="3", action="goto_screen_3", description="Steps", show=True),
        Binding(key="q", action="quit", description="Quit", show=True),
    ]

    def on_key(self, event: events.Key) -> None:
        """Common key handling with Input focus prevention."""       
        if event.key == "1":
            self.action_goto_screen_1()
        elif event.key == "2":
            self.action_goto_screen_2()
        elif event.key == "3":
            self.action_goto_screen_3()
        elif event.key == "q":
            self.app.exit()

    def action_goto_screen_1(self):
        self.app.push_screen('search')

    def action_goto_screen_2(self):
        self.app.push_screen('flows')

    def action_goto_screen_3(self):
        self.app.push_screen('steps')
        
    def on_active_flow_changed(self, event: ActiveFlowChanged):
        """Update header text when active flow changes"""
        header = self.query_one(FlowHeader)
        if event.flow_name == None:
            header.update("No active flow")
        else:
            # ai? how can we ensure headers on other screens are updated too?
            header.update(event.flow_name) 
