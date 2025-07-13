from datetime import datetime, timezone
import pytest
from textual.widgets import Static
from screens.base_screen import FlowHeader, ActiveFlowChanged, BaseScreen
from cli import RGApp
from db import get_db
import tempfile
import os

@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    schema_path = os.path.join(os.path.dirname(__file__), "../schema.sql")
    db = get_db(db_path, schema_path)
    yield db
    os.remove(db_path)

async def test_flow_header_component(db):
    """Test FlowHeader component functionality and message handling"""
    app = RGApp(db)
    
    # Create a minimal test screen
    class TestScreen(BaseScreen):
        def compose(self):
            yield FlowHeader()
    
    async with app.run_test() as pilot:
        # Push our test screen
        await pilot.app.push_screen(TestScreen())
        
        # Get the FlowHeader instance
        header = pilot.app.screen.query_one(FlowHeader)
        
        # 1. Test initial state
        assert isinstance(header, FlowHeader)
        assert header.renderable == "No active flow"
        
        # 2. Test message handling
        flow_name = "Test Flow 123"
        await pilot.app.screen.post_message(ActiveFlowChanged(flow_name))
        assert header.renderable == flow_name
        
        # 3. Test with None flow name
        await pilot.app.screen.post_message(ActiveFlowChanged(None))
        assert header.renderable == "No active flow"
        
        # 4. Test styling
        assert "background: dodgerblue" in header.DEFAULT_CSS
        assert "color: white" in header.DEFAULT_CSS
        assert header.styles.background == "dodgerblue"
        assert header.styles.color == "white"
