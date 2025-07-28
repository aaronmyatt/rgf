import pytest
from unittest.mock import patch
import os
import tempfile
from db import get_db
from cli import RGApp
from waystation import UserGrep

user_grep = UserGrep("test_pattern", ["."])

@pytest.fixture
def db():
    # Use a temporary file for the database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    schema_path = os.path.join(os.path.dirname(__file__), "../schema.sql")
    db = get_db(db_path, schema_path)
    yield db
    os.remove(db_path)

async def test_app_initialization_with_args(db):
    """Test that the app initializes correctly with UserGrep arguments."""
    user_grep = UserGrep("test_pattern", ["."])
    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        assert app.is_screen_installed("search")
        assert len(app.screen_stack) > 0
        assert app.user_grep == user_grep
        assert app.screen.id == "search"

async def test_initial_screen_is_search_when_pattern_provided_by_uesr(db):
    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        await pilot.press("escape")  # to clear initial input focus

        # Start on search screen
        assert app.screen.id == "search"

async def test_screen_navigation(db):
    """Test navigation between screens using key bindings."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("escape")  # to clear initial input focus

        # Start on search flows
        assert app.screen.id == "flows"
        
        # Navigate to screen 2
        await pilot.press("2")
        assert app.screen.id == "flows"
        
        # Navigate to screen 3
        await pilot.press("3")
        assert app.screen.id == "steps"
        
        # Navigate back to search screen
        await pilot.press("1")
        assert app.screen.id == "search"


# TODO - confusing test, needs to be fixed
@pytest.mark.skip(reason="This test is currently not working as expected")
async def test_screens_are_installed(db):
    """Test that all screens are properly installed."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        # Check that all screens are installed
        await pilot.press("2")
        await pilot.press("3")
        assert "search" in [screen.id for screen in app.screen_stack]
        assert "flows" in [screen.id for screen in app.screen_stack]
        assert "steps" in [screen.id for screen in app.screen_stack]


async def test_unfocus_all_action(db):
    """Test the unfocus all action works on all screens."""
    
    app = RGApp(db)
    async with app.run_test() as pilot:
        # Test on search screen
        await pilot.press("1")
        await pilot.press("escape")
        # Should not crash and should still be on search screen
        assert app.screen.id == "search"
        
        # Test on other screens
        await pilot.press("2")
        await pilot.press("escape")
        assert app.screen.id == "flows"
        
        await pilot.press("3")
        await pilot.press("escape")
        assert app.screen.id == "steps"

async def test_save_match_notification(db):
    """Test that saving a match shows a notification."""
    from app_actions import save_match
    from db import Match
    from waystation import UserGrep

    app = RGApp(db, UserGrep("test_some_async_operation", ["test_data/"]))
    async with app.run_test() as pilot:
        app.screen.dg.focus()

        with patch.object(app, 'notify') as mock_notify:
            # Trigger save action
            app.screen.action_save_match()

            # Verify notification
            mock_notify.assert_called_once()
            args, kwargs = mock_notify.call_args
            assert "Match saved" in args[0]
            assert kwargs.get("severity") == "information"

async def test_save_match_error_notification(db):
    """Test error notification when no match is selected."""
    app = RGApp(db)
    async with app.run_test() as pilot:
        await pilot.press("1")
        app.screen.dg.focus()

        with patch.object(app, 'notify') as mock_notify:
            app.screen.action_save_match()

            mock_notify.assert_called_once()
            args, kwargs = mock_notify.call_args
            assert "No matches available" in args[0]
            assert kwargs.get("severity") == "warning"

@pytest.mark.skip()
async def test_save_match_causes_saved_row_to_be_sorted_to_the_top(db):
    """Test error notification when no match is selected."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(db, user_grep)
    async with app.run_test() as pilot:
        assert len(app.screen.dg.ordered_rows) == len(app.screen.matches)
        
        row = app.screen.dg.ordered_rows[-1]
        real_row = app.screen.dg.get_row(row.key)
        assert real_row[0].plain == app.screen.matches[-1].file_name
        app.screen.dg.move_cursor(row=len(app.screen.dg.ordered_rows))

        app.screen.action_save_match()
        await pilot.pause()

        row = app.screen.dg.ordered_rows[0]
        real_row_after = app.screen.dg.get_row(row.key)

        assert len(list(db['matches'].rows)) == 1
        assert real_row_after[0].plain == app.screen.matches[0].file_name
        assert real_row_after[1].plain == str(app.screen.matches[0].line_no)
        assert real_row[0].plain == real_row_after[0].plain