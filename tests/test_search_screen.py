import pytest
from cli import RGApp
from waystation import UserGrep, Match
from textual.widgets import Input, DataTable


async def test_input_submission_returns_matches():
    app = RGApp()
    async with app.run_test() as pilot:
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = "async def test_some_async_operation"
        paths_input.value = "test_data/"

        await pilot.press("enter")
        assert len(app.screen.matches) == 1
        assert "test_data/sample_code.py" in app.screen.matches[0].filename
        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) == 1


async def test_search_screen_initialization_with_user_grep():
    """Test that the search screen initializes correctly with UserGrep arguments."""
    user_grep = UserGrep("test", ["test_data/"])
    app = RGApp(user_grep)
    async with app.run_test() as pilot:
        assert app.user_grep == user_grep
        assert len(app.screen.matches) > 0
        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) > 0


async def test_search_screen_initialization_without_args():
    """Test that the search screen focuses on pattern input when no args provided."""
    app = RGApp()
    async with app.run_test() as pilot:
        pattern_input = app.screen.query_one('#pattern_input')
        assert app.screen.focused == pattern_input

async def test_data_table_row_selection_updates_preview():
    """Test that selecting a row in the data table updates the preview."""
    user_grep = UserGrep("class", ["./test_data/"])
    app = RGApp(user_grep)
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


async def test_new_search_action():
    """Test that the new search action clears data and focuses input."""
    user_grep = UserGrep("test", ["test_data/"])
    app = RGApp(user_grep)
    async with app.run_test() as pilot:
        # Initially should have matches
        assert len(app.screen.matches) > 0

        # Trigger new search
        await pilot.press("n")

        # Should clear matches and focus pattern input
        pattern_input = app.screen.query_one('#pattern_input')
        assert pattern_input.value == ""
        assert len(app.screen.matches) == 0
        assert app.screen.focused == pattern_input

        datatable = app.screen.query_one('#matches_table')
        assert len(datatable.rows) == 0


async def test_empty_search_pattern():
    """Test behavior when submitting an empty search pattern."""
    app = RGApp()
    async with app.run_test() as pilot:
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = ""
        paths_input.value = "test_data/"

        await pilot.press("enter")
        
        # essentially searches for all files in the path
        assert len(app.screen.matches) > 0


async def test_search_with_multiple_paths():
    """Test searching across multiple paths."""
    app = RGApp()
    async with app.run_test() as pilot:
        pattern_input = app.screen.query_one('#pattern_input')
        paths_input = app.screen.query_one('#paths_input')

        pattern_input.value = "def"
        paths_input.value = "test_data/ tests/"

        await pilot.press("enter")
        # Should find matches in both directories
        assert len(app.screen.matches) > 0
        assert any("test_data/" in match.filename for match in app.screen.matches)
        assert any("tests/" in match.filename for match in app.screen.matches)



async def test_should_clear_data_table_on_resubmission():
    """Test behavior when search returns no matches."""
    app = RGApp()
    async with app.run_test() as pilot:
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

async def test_search_no_matches():
    """Test behavior when search returns no matches."""
    app = RGApp()
    async with app.run_test() as pilot:
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


async def test_escape_key_unfocuses_input():
    """Test that escape key unfocuses input fields."""
    app = RGApp()
    async with app.run_test() as pilot:
        pattern_input = app.screen.query_one('#pattern_input')
        pattern_input.focus()

        await pilot.press("escape")
        assert app.screen.focused != pattern_input


async def test_screen_navigation_blocked_when_input_focused():
    """Test that screen navigation keys are blocked when input is focused."""
    app = RGApp()
    async with app.run_test() as pilot:
        pattern_input = app.screen.query_one('#pattern_input')
        pattern_input.focus()

        # These should not trigger screen changes when input is focused
        await pilot.press("1")
        await pilot.press("2")
        await pilot.press("3")

        # Should still be on search screen
        assert app.screen.id == "search"
        assert pattern_input.value == "123"


async def test_preview_error_handling():
    """Test that preview handles errors gracefully."""
    app = RGApp()
    async with app.run_test() as pilot:
        # Create a scenario that might cause preview errors
        app.screen.matches = [Match("nonexistent.py", 1, "test content")]
        app.screen.update_preview(0)
        # Should not crash and should display error message
        assert app.screen.preview._content == "<no preview>"

async def test_open_in_editor_action():
    """Test the open in editor action (mocked)."""
    user_grep = UserGrep("def", ["test_data/"])
    app = RGApp(user_grep)
    async with app.run_test() as pilot:
        datatable = app.screen.query_one('#matches_table')
        datatable.focus()

        # Mock the system call to avoid actually opening an editor
        import unittest.mock
        app.suspend = unittest.mock.Mock()
        await pilot.press("enter")
        # Should have attempted to call system with editor command
        app.suspend.assert_called_once()