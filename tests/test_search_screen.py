from datetime import datetime, timedelta, timezone
import pytest
import os
import tempfile
from app_actions import get_active_flow_id
from db import get_db
from cli import RGApp
from waystation import UserGrep, Match

@pytest.fixture
def db():
    # Use a temporary file for the database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    schema_path = os.path.join(os.path.dirname(__file__), "../schema.sql")
    db = get_db(db_path, schema_path)
    yield db
    os.remove(db_path)

async def test_input_submission_returns_matches(db):
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("1")
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = "async def test_some_async_operation"
        paths_input.value = "test_data/"

        await pilot.press("enter")
        assert len(app.screen.matches) == 1
        assert "test_data/sample_code.py" in app.screen.matches[0].file_path
        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) == 1


async def test_search_screen_initialization_with_user_grep(db):
    """Test that the search screen initializes correctly with UserGrep arguments."""
    user_grep = UserGrep("test", ["test_data/"])
    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        assert app.user_grep == user_grep
        assert len(app.screen.matches) > 0
        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) > 0


async def test_search_screen_initialization_without_args(db):
    """Test that the search screen focuses on pattern input when no args provided."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")
        pattern_input = app.screen.query_one('#pattern_input')
        assert app.screen.focused == pattern_input

async def test_data_table_row_selection_updates_preview(db):
    """Test that selecting a row in the data table updates the preview."""
    user_grep = UserGrep("def", ["./test_data/"])
    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()

        preview1 = app.screen.query_one('#grep_ast_preview')._content
        assert preview1 is not None
        
        # Test cursor down
        await pilot.press("down")
        preview2 = app.screen.query_one('#grep_ast_preview')._content
        # Preview should be updated for the next row
        assert preview2 is not None
        assert preview2 != preview1

        # Test cursor up
        await pilot.press("up")
        preview11 = app.screen.query_one('#grep_ast_preview')._content
        assert preview11 is not None
        assert preview11 == preview1


async def test_new_search_action(db):
    """Test that the new search action clears data and focuses input."""
    user_grep = UserGrep("test", ["test_data/"])
    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        # Initially should have matches
        assert len(app.screen.matches) > 0

        # Trigger new search
        await pilot.press("/")

        # Should clear matches and focus pattern input
        pattern_input = app.screen.query_one('#pattern_input')
        assert pattern_input.value == ""
        assert len(app.screen.matches) == 0
        assert app.screen.focused == pattern_input

        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) == 0


async def test_empty_search_pattern(db):
    """Test behavior when submitting an empty search pattern."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = ""
        paths_input.value = "test_data/"

        await pilot.press("enter")
        
        # essentially searches for all files in the path
        assert len(app.screen.matches) > 0


async def test_search_with_multiple_paths(db):
    """Test searching across multiple paths."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = "def"
        paths_input.value = "test_data/ tests/"

        await pilot.press("enter")
        # Should find matches in both directories
        assert len(app.screen.matches) > 0
        assert any("test_data/" in match.file_path for match in app.screen.matches)
        assert any("tests/" in match.file_path for match in app.screen.matches)



async def test_should_clear_data_table_on_resubmission(db):
    """Test behavior when search returns no matches."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        # Initial search
        pattern_input.value = "def"
        paths_input.value = "test_data/"
        await pilot.press("enter")
        assert len(app.screen.matches) > 0

        # Resubmit same search
        pattern_input.focus()
        await pilot.press("enter")
        assert len(app.screen.matches) > 0  

async def test_search_no_matches(db):
    """Test behavior when search returns no matches."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = "nonexistent_pattern_xyz123"
        paths_input.value = "test_data/"

        await pilot.press("enter")
        assert len(app.screen.matches) == 0
        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) == 0
        preview = app.screen.query_one('#grep_ast_preview')._content
        assert preview == '<no preview>'  # No preview should be shown


async def test_escape_key_unfocuses_input(db):
    """Test that escape key unfocuses input fields."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")

        await pilot.press("escape")
        pattern_input = app.screen.query_one('#pattern_input')
        assert app.screen.focused != pattern_input


async def test_screen_navigation_blocked_when_input_focused(db):
    """Test that screen navigation keys are blocked when input is focused."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")

        # These should not trigger screen changes when input is focused
        await pilot.press("1")
        await pilot.press("2")
        await pilot.press("3")

        # Should still be on search screen
        assert app.screen.id == "search"
        pattern_input = app.screen.query_one('#pattern_input')
        assert pattern_input.value == "123"


async def test_preview_error_handling(db):
    """Test that preview handles errors gracefully."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")
        # Create a scenario that might cause preview errors
        app.screen.matches = [Match("nonexistent.py", 1, "test content")]
        app.screen.update_preview(0)
        # Should not crash and should display error message
        assert app.screen.preview._content == "<no preview>"

async def test_save_match_to_database_binding(db):
    """Test that pressing 's' saves the current match to the database."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)
    
    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()
        
        current_row = datatable.cursor_coordinate.row
        current_match = app.screen.matches[current_row]
        
        initial_count = len(db.execute("SELECT * FROM matches").fetchall())
        
        await pilot.press("s")
        
        matches = list(db.table('matches').rows)
        assert len(matches) == initial_count + 1
        
        saved_match = matches[-1]
        assert saved_match['file_path'] == current_match.file_path
        assert saved_match['line'] == current_match.line
        assert saved_match['file_name'] == current_match.file_name.split('/')[-1]
        assert saved_match['archived'] == 0  # Should be saved as active

async def test_save_match_creates_and_links_to_new_flow(db):
    """Test that pressing 's' saves the current match to the database."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)
    
    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()
              
        initial_count = len(db.execute("SELECT * FROM matches").fetchall())
        
        await pilot.press("s")
        
        matches = list(db.table('matches').rows)
        flow_matches = list(db.table('flow_matches').rows)
        flows = list(db.table('flows').rows)
        assert len(matches) == initial_count + 1
        assert len(flow_matches) == 1
        assert len(flows) == 1
        assert flow_matches[0]['flows_id'] == flows[0]['id']
        assert flow_matches[0]['matches_id'] == matches[-1]['id']

async def test_save_match_activates_newly_created_flow(db):
    """Test that pressing 's' saves the current match to the database."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)
    
    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()
        
        await pilot.press("s")
        flows = list(db.table('flows').rows)
        flow_id = get_active_flow_id(db, session_start=datetime.now(timezone.utc) - timedelta(minutes=1))
        assert flows[0]['id'] == flow_id, "The newly created flow should be active"

async def test_save_match_relates_to_already_active_flow(db):
    """Test that pressing 's' saves the current match to the database."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)
    
    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()
        
        await pilot.press("s")
        flows = list(db.table('flows').rows)
        flow_id = get_active_flow_id(db, session_start=datetime.now(timezone.utc) - timedelta(minutes=1))
        assert flows[0]['id'] == flow_id, "The newly created flow should be active"
        await pilot.press("down")
        await pilot.press("s")
        get_flows_and_matches = db.execute("""
            SELECT f.id, m.id FROM flows f
            JOIN flow_matches fm ON f.id = fm.flows_id
            JOIN matches m ON fm.matches_id = m.id
            WHERE f.id = ?
        """, (flow_id,)).fetchall()
        assert len(get_flows_and_matches) == 2, "The match should be added to the already active flow"

async def test_cursor_navigation_on_empty_datatable_does_not_throw_error(db):
    """Test that pressing up/down on an empty data table doesn't throw CellDoesNotExist error."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("/")
        # Ensure we start with an empty data table
        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) == 0
        assert len(app.screen.matches) == 0
        
        # Focus the data table
        datatable.focus()
        
        # These should not throw CellDoesNotExist errors
        await pilot.press("up")
        await pilot.press("down")
        await pilot.press("up")
        await pilot.press("down")
        
        # Should still have empty table and no crashes
        assert len(datatable.rows) == 0
        assert len(app.screen.matches) == 0


async def test_open_in_editor_action(db):
    """Test the open in editor action (mocked)."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()

        # Mock the system call to avoid actually opening an editor
        import unittest.mock
        app.suspend = unittest.mock.Mock()
        await pilot.press("shift+enter")
        # Should have attempted to call system with editor command
        app.suspend.assert_called_once()


async def test_match_highlighting_changes_with_active_flow(db):
    """Test that row highlighting updates when active flow changes"""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)

    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()

        # Save first match to Flow A
        await pilot.press("s")
        row_idx = datatable.cursor_coordinate.row
        row_key = datatable.ordered_rows[row_idx].key

        # Verify row is highlighted for Flow A
        for cell in datatable.get_row(row_key):
            assert any(["green" in str(span.style) for span in cell[0].spans]), "Row should be highlighted after saving"

        # Create Flow B
        await pilot.press("2")  # Go to FlowScreen
        await pilot.press("n")  # Create new flow
        name_input = app.screen.query_one("#flow_name_input")
        name_input.value = "Flow B"
        await pilot.press("enter")  # Submit new flow

        # Activate Flow B
        await pilot.press("enter")  # Select new flow
        await pilot.press("a")  # Activate flow

        # Return to SearchScreen
        await pilot.press("1")

        # TEST WILL FAIL HERE - row still highlighted for Flow A
        for cell in datatable.get_row(row_key):
            assert any(["green" not in str(span.style) for span in cell[0].spans]), "Row should NOT be highlighted for different flow"

        # Return to FlowScreen and activate Flow A again
        await pilot.press("2")
        flows_list = app.screen.query_one("#flows_list")
        flows_list.focus()
        await pilot.press("up")  # Select Flow A
        await pilot.press("a")  # Activate Flow A

        # Return to SearchScreen
        await pilot.press("1")

        # TEST WILL FAIL HERE - row not re-highlighted for Flow A
        for cell in datatable.get_row(row_key):
            assert any(["green" in str(span.style) for span in cell[0].spans]), "Row should be highlighted again when original flow is active"

@pytest.mark.asyncio
async def test_regex_search(db):
    """Test that regex patterns work in search"""
    # Setup regex pattern that matches Python function definitions
    regex_pattern = r"def\s+\w+\s*\("
    user_grep = UserGrep(regex_pattern, ["test_data/sample_code.py"])

    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        await pilot.pause(0.1)  # Wait for search to complete

        # Verify matches were found
        search_screen = app.screen
        assert len(search_screen.matches) > 0

        # Verify at least one match looks like a function definition
        has_function_def = any(
            "def " in match.line and "(" in match.line
            for match in search_screen.matches
        )
        assert has_function_def, "No function definitions found with regex"