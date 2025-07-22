from textual.binding import Binding
from textual.app import ComposeResult
from textual.widgets import Static, Footer, ListView, ListItem, TextArea, Label
from textual.containers import Container
from textual import events
from pathlib import Path
from .base_screen import BaseScreen, FlowHeader
from app_actions import get_active_flow_id, get_flow_matches
from db import Match, FlowMatch
from waystation import get_grep_ast_preview


def get_language_from_filename(filename: str) -> str:
    """Determine syntax highlighting language from file extension"""
    ext = Path(filename).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.sql': 'sql',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.sh': 'bash',
        '.rs': 'rust',
        '.go': 'go',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
    }
    return language_map.get(ext, 'text')


class StepScreen(BaseScreen):
    id = "steps"
    BINDINGS = BaseScreen.COMMON_BINDINGS + [
        ("r", "refresh_matches", "Refresh"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flow_matches = []
    
    def compose(self) -> ComposeResult:
        yield FlowHeader()
        yield ListView(id="matches_list")
        yield Footer()

    async def on_mount(self):
        self.update_flow_name_in_header()
        await self.load_flow_matches()

    async def on_screen_resume(self, event):
        await super().on_screen_resume(event)
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
        
        if not self.flow_matches:
            matches_list.append(ListItem(Label("No matches in this flow.")))
            return
            
        for match, flow_match in self.flow_matches:
            list_item = self.create_match_list_item(match, flow_match)
            matches_list.append(list_item)

    def create_match_list_item(self, match: Match, flow_match: FlowMatch) -> ListItem:
        """Create a ListItem with syntax-highlighted code for a match"""
        # Get context around the match using existing waystation function
        preview_text = get_grep_ast_preview(match)
        language = get_language_from_filename(match.file_name)
        
        # Create container with file info and code
        
        # File info header
        file_info = f"{match.file_name}:{match.line_no} (Order: {flow_match.order_index})"
               
        # Syntax highlighted code
        code_area = TextArea.code_editor(
            preview_text, 
            language='python',
            read_only=True,
            show_line_numbers=True,
            classes="h-auto"
        )
             
        return ListItem(
            Label(file_info),
            code_area,
            classes="h-auto"
        )

    def action_refresh_matches(self):
        """Refresh the matches list"""
        self.run_worker(self.load_flow_matches)
