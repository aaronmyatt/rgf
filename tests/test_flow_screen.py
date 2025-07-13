import pytest
from datetime import datetime, timezone
from textual.widgets import ListView, ListItem, Label
from screens.flow_screen import FlowScreen
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
        screen = FlowScreen()
        app.install_screen(screen, "test_flow_screen")
        await app.push_screen("test_flow_screen")
        
        # Wait for flows to load
        await pilot.pause()
        
        # Check that flows were loaded
        assert len(screen.flows) == 2
        assert screen.flows[0].name == "Test Flow 1"
        assert screen.flows[1].name == "Test Flow 2"
        
        # Check that ListView contains the flows
        flows_list = screen.query_one("#flows_list", ListView)
        assert len(flows_list.children) == 2


# async def test_flow_screen_shows_no_flows_message_when_empty(db):
#     """Test that appropriate message is shown when no flows exist."""
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         # Check that no flows message is displayed
#         flows_list = screen.query_one("#flows_list", ListView)
#         assert len(flows_list.children) == 1
        
#         list_item = flows_list.children[0]
#         label = list_item.children[0]
#         assert "No flows found" in label.renderable


# async def test_flow_screen_excludes_archived_flows(db, sample_flows):
#     """Test that archived flows are not displayed."""
#     # Create both archived and non-archived flows
#     for flow in sample_flows:
#         new_flow(db, flow)
    
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         # Should only show 2 non-archived flows
#         assert len(screen.flows) == 2
#         for flow in screen.flows:
#             assert not flow.archived


# async def test_flow_selection_updates_selected_flow(db, sample_flows):
#     """Test that selecting a flow updates the selected_flow property."""
#     # Create flows in database
#     for flow in sample_flows[:2]:
#         new_flow(db, flow)
    
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         flows_list = screen.query_one("#flows_list", ListView)
        
#         # Simulate highlighting first flow
#         flows_list.index = 0
#         flows_list.post_message(flows_list.Highlighted(flows_list, flows_list.children[0]))
        
#         await pilot.pause()
        
#         assert screen.selected_flow is not None
#         assert screen.selected_flow.name == "Test Flow 1"


# async def test_enter_key_activates_selected_flow(db, sample_flows):
#     """Test that pressing Enter activates the selected flow."""
#     # Create flow in database
#     flow_id = new_flow(db, sample_flows[0])
    
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         # Select first flow
#         flows_list = screen.query_one("#flows_list", ListView)
#         flows_list.index = 0
#         flows_list.post_message(flows_list.Highlighted(flows_list, flows_list.children[0]))
        
#         await pilot.pause()
        
#         # Press Enter
#         await pilot.press("enter")
        
#         # Check that flow was activated
#         active_flow_id = get_active_flow_id(db)
#         assert active_flow_id == flow_id


# async def test_a_key_activates_selected_flow(db, sample_flows):
#     """Test that pressing 'a' key activates the selected flow."""
#     # Create flow in database
#     flow_id = new_flow(db, sample_flows[0])
    
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         # Select first flow
#         flows_list = screen.query_one("#flows_list", ListView)
#         flows_list.index = 0
#         flows_list.post_message(flows_list.Highlighted(flows_list, flows_list.children[0]))
        
#         await pilot.pause()
        
#         # Press 'a' key
#         await pilot.press("a")
        
#         # Check that flow was activated
#         active_flow_id = get_active_flow_id(db)
#         assert active_flow_id == flow_id


# async def test_activation_shows_success_notification(db, sample_flows):
#     """Test that successful flow activation shows a notification."""
#     # Create flow in database
#     new_flow(db, sample_flows[0])
    
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         # Select first flow
#         flows_list = screen.query_one("#flows_list", ListView)
#         flows_list.index = 0
#         flows_list.post_message(flows_list.Highlighted(flows_list, flows_list.children[0]))
        
#         await pilot.pause()
        
#         # Press 'a' key to activate
#         await pilot.press("a")
        
#         # Check for notification (this would need to be verified through app state)
#         # The notification system in Textual is internal, so we verify the flow was activated
#         active_flow_id = get_active_flow_id(db)
#         assert active_flow_id is not None


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


# async def test_refresh_flows_action_reloads_flows(db, sample_flows):
#     """Test that refresh action reloads flows from database."""
#     app = RGApp(db)
#     async with app.run_test() as pilot:
#         screen = FlowScreen()
#         app.install_screen(screen, "test_flow_screen")
#         await app.push_screen("test_flow_screen")
        
#         await pilot.pause()
        
#         # Initially no flows
#         assert len(screen.flows) == 0
        
#         # Add a flow to database
#         new_flow(db, sample_flows[0])
        
#         # Press 'r' to refresh
#         await pilot.press("r")
#         await pilot.pause()
        
#         # Should now show the new flow
#         assert len(screen.flows) == 1
#         assert screen.flows[0].name == "Test Flow 1"


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
