import pytest
from datetime import datetime, timedelta, timezone
from textual.widgets import ListView, ListItem, Label
from screens.flow_screen import FlowScreen, Words
from db import Flow, get_db
from app_actions import new_flow, activate_flow, get_active_flow_id
from cli import RGApp


@pytest.fixture
def db():
    """Create a test database."""
    return get_db(":memory:")


@pytest.fixture
def sample_flows():
    """Create sample flows for testing."""
    return [
        Flow(
            id=None,
            name="Test Flow 1",
            created_at=datetime.now(timezone.utc).isoformat(),
            archived=False
        ),
        Flow(
            id=None,
            name="Test Flow 2", 
            created_at=datetime.now(timezone.utc).isoformat(),
            archived=False
        ),
        Flow(
            id=None,
            name="Archived Flow",
            created_at=datetime.now(timezone.utc).isoformat(),
            archived=True
        )
    ]


async def test_flow_screen_loads_flows_from_database(db, sample_flows):
    """Test that flows are loaded from database on mount."""
    # Create flows in database
    flow_ids = []
    for flow in sample_flows[:2]:  # Only non-archived flows
        flow_id = new_flow(db, flow)
        flow_ids.append(flow_id)
    
    # Create archived flow (should not appear)
    new_flow(db, sample_flows[2])
    
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("escape")
        await pilot.press("2")  # Navigate to FlowScreen
        
        # Wait for flows to load
        await pilot.pause()
        
        # Check that flows were loaded
        assert len(app.screen.flows) == 2
        assert app.screen.flows[0].name == "Test Flow 1"
        assert app.screen.flows[1].name == "Test Flow 2"
        
        # Check that ListView contains the flows
        flows_list = app.screen.query_one("#flows_list", ListView)
        assert len(flows_list.children) == 2


async def test_flow_screen_shows_no_flows_message_when_empty(db):
    """Test that appropriate message is shown when no flows exist."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("escape")
        await pilot.press("2")  # Navigate to FlowScreen
        
        await pilot.pause()
        
        # Check that no flows message is displayed
        flows_list = app.screen.query_one("#flows_list", ListView)
        assert len(flows_list.children) == 1
        
        list_item = flows_list.children[0]
        label = list_item.children[0]
        assert Words.NO_FLOWS_MESSAGE in label.renderable


async def test_enter_key_activates_selected_flow(db, sample_flows):
    """Test that pressing Enter activates the selected flow."""
    # Create flow in database
    flow_id = new_flow(db, sample_flows[0])
    flow_id1 = new_flow(db, sample_flows[1])
    
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("escape")
        await pilot.press("2")  # Navigate to FlowScreen
        assert len(app.screen.flows) == 2
        
        await pilot.pause()
        
        # Select first flow
        await pilot.press("down")  # Navigate to FlowScreen
        await pilot.pause()
        
        # Press Enter
        await pilot.press("enter")
        
        # Check that flow was activated
        active_flow_id = get_active_flow_id(db, app.session_start - timedelta(seconds=1))
        assert active_flow_id == flow_id

        # Select second flow
        await pilot.press("down")  # Navigate to FlowScreen
        await pilot.pause()

                # Press Enter
        await pilot.press("a")
        
        # Check that flow was activated
        active_flow_id = get_active_flow_id(db, app.session_start - timedelta(seconds=1))
        assert active_flow_id == flow_id1


# async def test_activation_without_selected_flow_does_nothing(db):
#     """Test that activation without a selected flow does nothing."""
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         # No flow selected, press 'a'
#         await pilot.press("a")
        
#         # Should not activate any flow
#         active_flow_id = get_active_flow_id(db)
#         assert active_flow_id is None


async def test_refresh_flows_action_reloads_flows(db, sample_flows):
    """Test that refresh action reloads flows from database."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("escape")
        await pilot.press("2")  # Navigate to FlowScreen
        
        await pilot.pause()
        
        # Initially no flows
        assert len(app.screen.flows) == 0
        
        # Add a flow to database
        new_flow(db, sample_flows[0])
        
        # Press 'r' to refresh
        await pilot.press("r")
        await pilot.pause()
        
        # Should now show the new flow
        assert len(app.screen.flows) == 1
        assert app.screen.flows[0].name == "Test Flow 1"
        list_items = app.screen.query('.flow_list_item')
        assert len(list_items) == 1


# async def test_flow_display_includes_creation_date(db, sample_flows):
#     """Test that flow display includes creation date."""
#     # Create flow in database
#     new_flow(db, sample_flows[0])
    
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         flows_list = screen.query_one("#flows_list", ListView)
#         list_item = flows_list.children[0]
#         label = list_item.children[0]
        
#         # Check that label contains both name and creation date
#         label_text = str(label.renderable)
#         assert "Test Flow 1" in label_text
#         assert "Created:" in label_text


# async def test_database_error_handling(db):
#     """Test that database errors are handled gracefully."""
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
        
#         # Close the database to simulate an error
#         db.close()
        
#         await app.push_screen("test_flow_screen")
#         await pilot.pause()
        
#         # Should show error message instead of crashing
#         flows_list = screen.query_one("#flows_list", ListView)
#         assert len(flows_list.children) == 1
        
#         list_item = flows_list.children[0]
#         label = list_item.children[0]
#         assert "Error loading flows" in str(label.renderable)
