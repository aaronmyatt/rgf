import pytest
from cli import RGApp
from waystation import UserGrep


async def test_app_initialization():
    """Test that the app initializes correctly without arguments."""
    app = RGApp()
    async with app.run_test() as pilot:
        assert app.user_grep is None
        assert app.screen.id == "search"


async def test_app_initialization_with_args():
    """Test that the app initializes correctly with UserGrep arguments."""
    user_grep = UserGrep("test_pattern", ["test_path"])
    app = RGApp(user_grep)
    async with app.run_test() as pilot:
        assert app.user_grep == user_grep
        assert app.screen.id == "search"


async def test_screen_navigation():
    """Test navigation between screens using key bindings."""
    app = RGApp()
    async with app.run_test() as pilot:
        # Start on search screen
        assert app.screen.id == "search"
        
        # Navigate to screen 2
        await pilot.press("2")
        assert app.screen.id == "blank2"
        
        # Navigate to screen 3
        await pilot.press("3")
        assert app.screen.id == "blank3"
        
        # Navigate back to search screen
        await pilot.press("1")
        assert app.screen.id == "search"


async def test_screens_are_installed():
    """Test that all screens are properly installed."""
    app = RGApp()
    async with app.run_test() as pilot:
        # Check that all screens are installed
        assert "search" in app.screen_stack
        assert "blank2" in app.screen_stack
        assert "blank3" in app.screen_stack


async def test_unfocus_all_action():
    """Test the unfocus all action works on all screens."""
    app = RGApp()
    async with app.run_test() as pilot:
        # Test on search screen
        await pilot.press("escape")
        # Should not crash and should still be on search screen
        assert app.screen.id == "search"
        
        # Test on other screens
        await pilot.press("2")
        await pilot.press("escape")
        assert app.screen.id == "blank2"
        
        await pilot.press("3")
        await pilot.press("escape")
        assert app.screen.id == "blank3"
