import pytest
from datetime import datetime, timedelta, timezone
from textual.widgets import ListView, ListItem, Label, Input, TextArea, Button
from screens.flow_screen import FlowScreen, Words
from db import Flow, get_db, get_row
from app_actions import new_flow, activate_flow, get_active_flow_id
from cli import RGApp
from waystation import UserGrep


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
        assert len(app.screen.flows) == 2
               
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

@pytest.mark.asyncio
async def test_refresh_flows_with_last_item_selected_does_not_crash(db, sample_flows):
    """Test that refreshing flows with last item selected does not crash."""
    # Add two flows
    new_flow(db, sample_flows[0])
    new_flow(db, sample_flows[1])

    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("escape")
        await pilot.press("2")  # Go to FlowScreen
        await pilot.pause()

        # Select the last item (second flow)
        await pilot.press("down")
        await pilot.pause()

        # Refresh the flows list (no changes to DB)
        # If the bug is not fixed, this will raise an exception and the test will fail
        await pilot.press("r")
        await pilot.pause()

        # Optionally, check that the screen is still responsive and shows both flows
        assert len(app.screen.flows) == 2
        assert app.screen.flows[0].name == "Test Flow 1"
        assert app.screen.flows[1].name == "Test Flow 2"

async def test_edit_flow_name_and_description(db, sample_flows):
    """Test editing a flow's name and description."""
    # Insert sample flow
    flow_id = new_flow(db, sample_flows[0])
    
    app = RGApp(db)
    async with app.run_test() as pilot:
        # Navigate to FlowScreen
        await pilot.press("escape")
        await pilot.press("2")
        await pilot.pause()  # Wait for flows to load
        
        # Verify initial flow name
        flows_list = app.screen.query_one("#flows_list", ListView)
        list_item = flows_list.children[0]
        await pilot.click(list_item)
        

        initial_label = list_item.query_one(Label).renderable
        assert sample_flows[0].name in initial_label
        assert app.screen.selected_flow is not None
        
        # Press 'e' to edit the flow
        await pilot.press("e")
        await pilot.pause()  # Wait for overlay to appear

        # Update name and description
        overlay = app.screen.query_one("#flow_edit_overlay")
        name_input = overlay.query_one("#flow_name_input", Input)
        desc_input = overlay.query_one("#flow_description_input", TextArea)
        
        new_name = "Updated Flow Name"
        new_desc = "This is an updated description"
        
        name_input.value = new_name
        desc_input.text = new_desc
        
        # Press Save button
        save_button = overlay.query_one("#save_flow_button", Button)
        save_button.action_press()
        await pilot.pause()  # Wait for save to complete
        
        # Verify database update
        updated_flow = get_row(db, "flows", flow_id, Flow)
        assert updated_flow.name == new_name
        assert updated_flow.description == new_desc
        
        # Verify UI update
        list_item = flows_list.children[0]
        updated_label = list_item.query_one(Label).renderable
        assert new_name in updated_label
        assert new_name not in initial_label  # Verify change occurred

@pytest.mark.skip()
async def test_flow_match_count_updates_after_saving_matches(db):
    """Test that saving matches updates flow match counts in FlowScreen."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)

    async with app.run_test() as pilot:
        # Save first match
        await pilot.press("s")

        # Navigate to FlowScreen (key "2")
        await pilot.press("2")
        flow_screen = app.screen

        # Find the flow list item
        flows_list = flow_screen.query_one(ListView)
        first_flow_item = flows_list.children[0].children[0].renderable


        # Verify match count shows "1 match"
        assert "1 match" in first_flow_item

        # Navigate back to SearchScreen (key "1")
        await pilot.press("1")

        # Save second match
        await pilot.press("down")  # Move to next match
        await pilot.press("s")     # Save second match

        assert len(list(db['matches'].rows)) == 2

  
        # Navigate back to FlowScreen
        await pilot.press("2")
        await pilot.pause()
        flow_screen = app.screen
        
        # Find the flow list item again
        flows_list_again = flow_screen.query_one(ListView)
        first_flow_item_after = flows_list_again.children[0].children[0].renderable

        assert "2 matches" in first_flow_item_after