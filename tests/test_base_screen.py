from datetime import datetime, timezone
import pytest
from textual.widgets._header import HeaderTitle
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
    
    async with app.run_test() as pilot:
        await pilot.pause()
        # Get the FlowHeader instance
        header = app.screen.query_exactly_one(FlowHeader)
        title = header.query_exactly_one(HeaderTitle)
        
        # 1. Test initial state
        assert isinstance(header, FlowHeader)
        assert title.text == "No active flow"
        
        # 2. Test message handling
        flow_name = "Test Flow 123"
        app.screen.post_message(ActiveFlowChanged(flow_name))
        await pilot.pause()
        assert title.text == flow_name
        
        # 3. Test with None flow name
        app.screen.post_message(ActiveFlowChanged(None))
        await pilot.pause()
        assert title.text == "No active flow"
