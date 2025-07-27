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

    async def on_click(self, event) -> None:
        """Activate a tab that was clicked."""
        if isinstance(event.widget, Tab):
            await self.app.push_screen(event.widget.id)


class BaseScreen(Screen):
    """Base screen with common navigation functionality."""

    BINDINGS = [
        Binding(key="1", action="goto_screen('search')", description="Search", show=False),
        Binding(key="2", action="goto_screen('flows')", description="Flows", show=False),
        Binding(key="3", action="goto_screen('steps')", description="Steps", show=False),
        Binding(key="q", action="quit", description="Quit", show=True),
        # Add this new binding for quick search access
        Binding(key="/", action="goto_screen('search')", description="Search", show=True),
    ]

    async def action_goto_screen(self, screen: str):
        """Action to navigate to search screen"""
        await self.app.push_screen(screen)
        tab = self.query_one(f"#{screen}", Tab)
        self.query_one(Tabs)._activate_tab(tab)

    # async def on_tabs_tab_activated(self, event):
    #     await self.app.push_screen(event.tab.id)

    async def on_key(self, event: events.Key) -> None:
        """Common key handling with Input focus prevention."""       
        if event.key == "1":
            await self.action_goto_screen('search')
        elif event.key == "2":
            await self.action_goto_screen('flows')
        elif event.key == "3":
            await self.action_goto_screen('steps')

    async def action_quit(self):
        await self.app.action_quit()
        
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
